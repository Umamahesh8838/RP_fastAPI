"""Orchestrator service: coordinates resume extraction, parsing, and persistence.

Includes timing instrumentation for the main public entrypoints:
- run_full_pipeline: full 15-step save flow
- parse_resume_preview: preview parsing with caching (no DB writes)
- save_confirmed_resume: apply user-confirmed parsed data to DB (steps 4-15)
"""

import logging
import time
import asyncio
from datetime import datetime
from typing import Dict, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError

from schemas.parse_schema import ParsedResume
from schemas.student_schema import SaveStudentRequest
from schemas.education_schema import SaveSchoolRequest, SaveEducationRequest
from schemas.workexp_schema import SaveWorkExpRequest
from schemas.project_schema import SaveProjectRequest
from schemas.address_schema import SaveAddressRequest
from utils.hash_utils import compute_resume_hash
from utils import cache_utils
from services import extract_service, llm_service, lookup_service, save_service

logger = logging.getLogger(__name__)


async def _execute_with_db_retry(db: AsyncSession, sql_text, params: dict, retries: int = 3):
	"""Retry transient DB connection timeouts (common with Azure SQL serverless cold starts)."""
	last_err = None
	for attempt in range(1, retries + 1):
		try:
			return await db.execute(sql_text, params)
		except OperationalError as e:
			last_err = e
			err_text = str(e).lower()
			if "hyt00" not in err_text and "login timeout expired" not in err_text:
				raise
			if attempt >= retries:
				break
			wait_s = attempt * 5
			logger.warning(f"Transient DB timeout detected. Retrying in {wait_s}s (attempt {attempt}/{retries})")
			await asyncio.sleep(wait_s)

	raise last_err


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------
async def run_full_pipeline(db: AsyncSession, file_bytes: bytes, filename: str) -> Dict[str, Any]:
	"""Run the full resume pipeline (steps 1-15) with timing breakdown."""

	warnings = []
	summary = {
		"schools_saved": 0,
		"educations_saved": 0,
		"workexps_saved": 0,
		"projects_saved": 0,
		"skills_saved": 0,
		"languages_saved": 0,
		"certifications_saved": 0,
		"interests_saved": 0,
		"addresses_saved": 0,
	}

	overall_start = time.perf_counter()
	t_extract = t_hash = t_pass1 = t_pass2 = 0.0

	# STEP 1 — Extract text
	logger.info("STEP 1 — Extract text")
	step_start = time.time()
	try:
		file_ext = filename.lower().split(".")[-1] if "." in filename else ""
		if file_ext == "pdf":
			extract_result = await extract_service.extract_text_from_pdf(file_bytes)
		elif file_ext == "docx":
			extract_result = await extract_service.extract_text_from_docx(file_bytes)
		else:
			raise ValueError("Unsupported file type. Please upload a PDF or DOCX file.")

		resume_text = extract_result["text"]
		char_count = extract_result.get("char_count", len(resume_text or ""))
		t_extract = time.time() - step_start
		print(f"[TIMING] Text extraction: {t_extract:.2f} seconds")
		logger.info(f"Step 1 complete: extracted {char_count} chars")
	except Exception as e:
		logger.error(f"Step 1 failed: {e}")
		raise ValueError(f"Text extraction failed: {e}")

	# STEP 2 — Duplicate check
	logger.info("STEP 2 — Duplicate check")
	step_start = time.time()
	try:
		resume_hash = compute_resume_hash(resume_text)
		result = await _execute_with_db_retry(
			db,
			text("SELECT student_id FROM tbl_cp_resume_hashes WHERE hash = :hash"),
			{"hash": resume_hash},
		)
		existing_hash = result.fetchone()
		t_hash = time.time() - step_start
		print(f"[TIMING] Hash check: {t_hash:.2f} seconds")

		if existing_hash:
			logger.info(f"Resume already processed, student_id={existing_hash[0]}")
			total_elapsed = time.perf_counter() - overall_start
			print(
				f"[TIMING SUMMARY] Text extraction={t_extract:.2f}s | Hash check={t_hash:.2f}s | TOTAL={total_elapsed:.2f}s"
			)
			return {
				"student_id": existing_hash[0],
				"resume_hash": resume_hash,
				"already_existed": True,
				"message": "Resume already processed",
			}
	except Exception as e:
		logger.error(f"Step 2 failed: {e}")
		raise ValueError(f"Duplicate check failed: {e}")

	# STEP 3 — LLM parse (two-pass logical)
	logger.info("STEP 3 — LLM Parse (two-pass)")
	print("[STEP 3] Calling LLM (two-pass)")
	llm_start = time.perf_counter()
	try:
		parsed: ParsedResume = await llm_service.parse_resume_text(resume_text)
	except Exception as e:
		logger.error(f"Step 3 failed: {e}")
		raise ValueError(f"LLM parsing failed: {e}")
	llm_elapsed = time.perf_counter() - llm_start
	t_pass1 = t_pass2 = llm_elapsed / 2 if llm_elapsed > 0 else 0.0
	print(f"[TIMING] LLM total: {llm_elapsed:.2f} seconds (Pass1={t_pass1:.2f}s, Pass2={t_pass2:.2f}s)")

	# STEP 4 — Save student core record
	logger.info("STEP 4 — Save student core record")
	try:
		salutation_id = None
		if parsed.salutation:
			sal_result = await lookup_service.find_salutation(db, parsed.salutation)
			if getattr(sal_result, "found", False):
				salutation_id = sal_result.salutation_id

		student_request = SaveStudentRequest(
			salutation_id=salutation_id,
			first_name=parsed.first_name,
			middle_name=parsed.middle_name,
			last_name=parsed.last_name,
			email=parsed.email,
			alt_email=parsed.alt_email,
			contact_number=parsed.contact_number,
			alt_contact_number=parsed.alt_contact_number,
			linkedin_url=parsed.linkedin_url,
			github_url=parsed.github_url,
			portfolio_url=parsed.portfolio_url,
			date_of_birth=parsed.date_of_birth,
			current_city=parsed.current_city,
			gender=parsed.gender,
		)
		student_result = await save_service.save_student(db, student_request)
		student_id = student_result.student_id
		already_existed = student_result.already_exists
		logger.info(f"Student saved: id={student_id}, already_existed={already_existed}")
	except Exception as e:
		logger.error(f"Step 4 failed: {e}")
		raise ValueError(f"Student save failed: {e}")

	# STEP 5 — Save school records
	logger.info("STEP 5 — Save school records")
	try:
		for school_item in parsed.school:
			if not school_item.standard:
				continue
			try:
				await save_service.save_school(
					db,
					SaveSchoolRequest(
						student_id=student_id,
						standard=school_item.standard,
						board=school_item.board,
						school_name=school_item.school_name,
						percentage=school_item.percentage,
						passing_year=school_item.passing_year,
					),
				)
				summary["schools_saved"] += 1
			except Exception as e:
				logger.warning(f"Failed to save school: {e}")
				warnings.append(f"School save failed: {e}")
	except Exception as e:
		logger.warning(f"Step 5 warning: {e}")

	# STEP 6 — Save college education
	logger.info("STEP 6 — Save college education")
	try:
		for edu_item in parsed.education:
			if not edu_item.college_name or not edu_item.course_name:
				continue
			try:
				college_result = await lookup_service.find_or_create_college(db, edu_item.college_name)
				course_result = await lookup_service.find_or_create_course(
					db,
					edu_item.course_name,
					edu_item.specialization_name or "General",
				)
				await save_service.save_education(
					db,
					SaveEducationRequest(
						student_id=student_id,
						college_id=college_result.college_id,
						course_id=course_result.course_id,
						start_year=edu_item.start_year,
						end_year=edu_item.end_year,
						cgpa=edu_item.cgpa,
						percentage=edu_item.percentage,
					),
				)
				summary["educations_saved"] += 1
			except Exception as e:
				logger.warning(f"Failed to save education: {e}")
				warnings.append(f"Education save failed: {e}")
	except Exception as e:
		logger.warning(f"Step 6 warning: {e}")

	# STEP 7 — Save work experience
	logger.info("STEP 7 — Save work experience")
	workexp_map = {}
	try:
		for exp_item in parsed.workexp:
			if not exp_item.company_name:
				continue
			try:
				result = await save_service.save_workexp(
					db,
					SaveWorkExpRequest(
						student_id=student_id,
						company_name=exp_item.company_name,
						company_location=exp_item.company_location,
						designation=exp_item.designation,
						employment_type=exp_item.employment_type,
						start_date=exp_item.start_date,
						end_date=exp_item.end_date,
						is_current=exp_item.is_current,
					),
				)
				workexp_map[exp_item.company_name] = result.workexp_id
				summary["workexps_saved"] += 1
			except Exception as e:
				logger.warning(f"Failed to save workexp: {e}")
				warnings.append(f"Work experience save failed: {e}")
	except Exception as e:
		logger.warning(f"Step 7 warning: {e}")

	# STEP 8 — Save projects + project skills
	logger.info("STEP 8 — Save projects + project skills")
	try:
		for proj_item in parsed.projects:
			if not proj_item.project_title:
				continue
			try:
				linked_workexp_id = None
				if proj_item.workexp_company_name:
					linked_workexp_id = workexp_map.get(proj_item.workexp_company_name)

				proj_result = await save_service.save_project(
					db,
					SaveProjectRequest(
						student_id=student_id,
						workexp_id=linked_workexp_id,
						project_title=proj_item.project_title,
						project_description=proj_item.project_description,
						achievements=proj_item.achievements,
						project_start_date=proj_item.project_start_date,
						project_end_date=proj_item.project_end_date,
					),
				)
				summary["projects_saved"] += 1

				for skill_name in proj_item.skills_used:
					if not skill_name:
						continue
					try:
						skill_result = await lookup_service.find_or_create_skill(db, skill_name, "Intermediate")
						await save_service.save_project_skill(db, proj_result.project_id, skill_result.skill_id)
					except Exception as e:
						logger.warning(f"Failed to save project skill: {e}")
						warnings.append(f"Project skill save failed: {e}")
			except Exception as e:
				logger.warning(f"Failed to save project: {e}")
				warnings.append(f"Project save failed: {e}")
	except Exception as e:
		logger.warning(f"Step 8 warning: {e}")

	# STEP 9 — Save student skills
	logger.info("STEP 9 — Save student skills")
	try:
		for skill_item in parsed.skills:
			if not skill_item.name:
				continue
			try:
				skill_result = await lookup_service.find_or_create_skill(
					db, skill_item.name, skill_item.complexity or "Intermediate"
				)
				await save_service.save_student_skill(db, student_id, skill_result.skill_id)
				summary["skills_saved"] += 1
			except Exception as e:
				logger.warning(f"Failed to save student skill: {e}")
				warnings.append(f"Student skill save failed: {e}")
	except Exception as e:
		logger.warning(f"Step 9 warning: {e}")

	# STEP 10 — Save languages
	logger.info("STEP 10 — Save languages")
	try:
		for lang_item in parsed.languages:
			if not lang_item.language_name:
				continue
			try:
				lang_result = await lookup_service.find_or_create_language(db, lang_item.language_name)
				await save_service.save_student_language(db, student_id, lang_result.language_id)
				summary["languages_saved"] += 1
			except Exception as e:
				logger.warning(f"Failed to save student language: {e}")
				warnings.append(f"Language save failed: {e}")
	except Exception as e:
		logger.warning(f"Step 10 warning: {e}")

	# STEP 11 — Save certifications
	logger.info("STEP 11 — Save certifications")
	try:
		for cert_item in parsed.certifications:
			if not cert_item.certification_name or not cert_item.issuing_organization:
				continue
			try:
				cert_result = await lookup_service.find_or_create_certification(
					db,
					cert_item.certification_name,
					cert_item.issuing_organization,
					cert_item.certification_type or "General",
					cert_item.is_lifetime,
				)
				await save_service.save_student_certification(
					db,
					{
						"student_id": student_id,
						"certification_id": cert_result.certification_id,
						"issue_date": cert_item.issue_date,
						"expiry_date": cert_item.expiry_date,
						"certificate_url": cert_item.certificate_url,
						"credential_id": cert_item.credential_id,
					},
				)
				summary["certifications_saved"] += 1
			except Exception as e:
				logger.warning(f"Failed to save certification: {e}")
				warnings.append(f"Certification save failed: {e}")
	except Exception as e:
		logger.warning(f"Step 11 warning: {e}")

	# STEP 12 — Save interests
	logger.info("STEP 12 — Save interests")
	try:
		for interest_item in parsed.interests:
			if not interest_item.name:
				continue
			try:
				interest_result = await lookup_service.find_or_create_interest(db, interest_item.name)
				await save_service.save_student_interest(db, student_id, interest_result.interest_id)
				summary["interests_saved"] += 1
			except Exception as e:
				logger.warning(f"Failed to save interest: {e}")
				warnings.append(f"Interest save failed: {e}")
	except Exception as e:
		logger.warning(f"Step 12 warning: {e}")

	# STEP 13 — Save addresses
	logger.info("STEP 13 — Save addresses")
	try:
		for addr_item in parsed.addresses:
			if not addr_item.address_line_1 or not addr_item.pincode:
				continue
			try:
				pincode_result = await lookup_service.find_pincode(db, addr_item.pincode)
				if not getattr(pincode_result, "found", False):
					warnings.append(f"Pincode {addr_item.pincode} not found. Address skipped.")
					continue

				await save_service.save_address(
					db,
					SaveAddressRequest(
						student_id=student_id,
						address_line_1=addr_item.address_line_1,
						address_line_2=addr_item.address_line_2,
						landmark=addr_item.landmark,
						pincode_id=pincode_result.pincode_id,
						address_type=addr_item.address_type or "current",
					),
				)
				summary["addresses_saved"] += 1
			except Exception as e:
				logger.warning(f"Failed to save address: {e}")
				warnings.append(f"Address save failed: {e}")
	except Exception as e:
		logger.warning(f"Step 13 warning: {e}")

	# STEP 14 — Store resume hash
	logger.info("STEP 14 — Store resume hash")
	try:
		await db.execute(
			text("INSERT INTO tbl_cp_resume_hashes (hash, student_id) VALUES (:hash, :student_id)"),
			{"hash": resume_hash, "student_id": student_id},
		)
		await db.commit()
	except Exception as e:
		logger.warning(f"Resume hash storage failed: {e}")
		warnings.append(f"Resume hash storage failed: {e}")

	total_elapsed = time.perf_counter() - overall_start
	print("=" * 50)
	print("[FULL PIPELINE TIMING]")
	print(f"  Text extraction : {t_extract:.2f}s")
	print(f"  Hash check      : {t_hash:.2f}s")
	print(f"  LLM Pass 1      : {t_pass1:.2f}s")
	print(f"  LLM Pass 2      : {t_pass2:.2f}s")
	print(f"  TOTAL           : {total_elapsed:.2f}s")
	print("=" * 50)

	return {
		"student_id": student_id,
		"resume_hash": resume_hash,
		"already_existed": already_existed,
		"summary": summary,
		"warnings": warnings,
	}


# ---------------------------------------------------------------------------
# Preview pipeline (no DB writes)
# ---------------------------------------------------------------------------
async def parse_resume_preview(db: AsyncSession, file_bytes: bytes, filename: str) -> Dict[str, Any]:
	"""Parse resume for preview with caching and timing; no DB writes."""

	overall_start = time.perf_counter()
	t_extract = t_hash = t_pass1 = t_pass2 = t_cache = 0.0

	print("=" * 60)
	print("[RESUME PARSER] Starting pipeline")
	print(f"[RESUME PARSER] File: {filename}")
	print(f"[RESUME PARSER] Time: {datetime.now().strftime('%H:%M:%S')}")
	print("=" * 60)

	# STEP 1 — Extract text
	logger.info("STEP 1 — Extract text (preview)")
	step_start = time.time()
	try:
		file_ext = filename.lower().split(".")[-1] if "." in filename else ""
		if file_ext == "pdf":
			extract_result = await extract_service.extract_text_from_pdf(file_bytes)
		elif file_ext == "docx":
			extract_result = await extract_service.extract_text_from_docx(file_bytes)
		else:
			raise ValueError("Unsupported file type. Please upload a PDF or DOCX file.")

		resume_text = extract_result["text"]
		char_count = extract_result.get("char_count", len(resume_text or ""))
		t_extract = time.time() - step_start
		print(f"[TIMING] Text extraction: {t_extract:.2f} seconds")
		logger.info(f"Preview extraction complete: {char_count} chars")
	except Exception as e:
		logger.error(f"Preview extraction failed: {e}")
		raise ValueError(f"Text extraction failed: {e}")

	# STEP 2 — Duplicate + cache check
	logger.info("STEP 2 — Duplicate + cache check (preview)")
	step_start = time.time()
	try:
		resume_hash = compute_resume_hash(resume_text)
		result = await _execute_with_db_retry(
			db,
			text("SELECT student_id FROM tbl_cp_resume_hashes WHERE hash = :hash"),
			{"hash": resume_hash},
		)
		existing_hash = result.fetchone()
		already_exists = existing_hash is not None
		t_hash = time.time() - step_start
		print(f"[TIMING] Hash check: {t_hash:.2f} seconds")

		cached = cache_utils.load_from_cache(resume_hash)
		if cached:
			parsed_block = cached.get("parsed", {}) if isinstance(cached, dict) else {}
			total_elapsed = time.perf_counter() - overall_start
			print("[CACHE HIT] Returning cached preview result")
			print(f"[RESUME PARSER] Total time: {total_elapsed:.1f}s | Hash: {resume_hash}")
			cached["already_exists"] = already_exists
			cached["resume_hash"] = resume_hash
			return cached
	except Exception as e:
		logger.error(f"Preview duplicate check failed: {e}")
		raise ValueError(f"Duplicate check failed: {e}")

	# STEP 3 — LLM parse (two-pass logical)
	logger.info("STEP 3 — LLM Parse (preview)")
	print("[STEP 3] Calling LLM (two-pass)")
	llm_start = time.perf_counter()
	try:
		parsed: ParsedResume = await llm_service.parse_resume_text(resume_text)
	except Exception as e:
		logger.error(f"Preview LLM parse failed: {e}")
		raise ValueError(f"LLM parsing failed: {e}")
	llm_elapsed = time.perf_counter() - llm_start
	t_pass1 = t_pass2 = llm_elapsed / 2 if llm_elapsed > 0 else 0.0
	parsed_dict = parsed.model_dump() if hasattr(parsed, "model_dump") else parsed
	print(f"[TIMING] LLM total: {llm_elapsed:.2f} seconds (Pass1={t_pass1:.2f}s, Pass2={t_pass2:.2f}s)")

	# STEP 4 — Calculate quality score
	from utils.quality_score import calculate_resume_quality
	
	quality = calculate_resume_quality(parsed_dict)
	print(f"[QUALITY] Resume score: {quality['score']}/100")
	print(f"[QUALITY] Grade: {quality['grade']} - {quality['grade_label']}")
	
	# STEP 5 — Cache save
	cache_data = {
		"resume_hash": resume_hash,
		"already_exists": already_exists,
		"parsed": parsed_dict,
		"quality": quality
	}
	step_start = time.time()
	cache_utils.save_to_cache(resume_hash, cache_data)
	t_cache = time.time() - step_start
	print(f"[TIMING] Cache save: {t_cache:.2f} seconds")

	# Calculate total elapsed time
	total_elapsed = time.perf_counter() - overall_start

	print("=" * 50)
	print("[TIMING SUMMARY]")
	print(f"  Text extraction : {t_extract:.2f}s")
	print(f"  Hash check      : {t_hash:.2f}s")
	print(f"  LLM Pass 1      : {t_pass1:.2f}s")
	print(f"  LLM Pass 2      : {t_pass2:.2f}s")
	print(f"  Cache save      : {t_cache:.2f}s")
	print(f"  TOTAL           : {total_elapsed:.2f}s")
	print("=" * 50)

	logger.info("Preview pipeline complete")
	return {
		"resume_hash": resume_hash,
		"already_exists": already_exists,
		"parsed": parsed_dict,
		"quality": quality
	}


# ---------------------------------------------------------------------------
# Save confirmed (no extraction/LLM, steps 4-15)
# ---------------------------------------------------------------------------
async def save_confirmed_resume(db: AsyncSession, resume_hash: str, parsed: ParsedResume) -> Dict[str, Any]:
	"""Save a confirmed ParsedResume to the database (steps 4-15)."""

	warnings = []
	summary = {
		"schools_saved": 0,
		"educations_saved": 0,
		"workexps_saved": 0,
		"projects_saved": 0,
		"skills_saved": 0,
		"languages_saved": 0,
		"certifications_saved": 0,
		"interests_saved": 0,
		"addresses_saved": 0,
	}

	# If parsed comes as dict, coerce to ParsedResume for attribute access
	if isinstance(parsed, dict):
		parsed = ParsedResume(**parsed)

	try:
		result = await db.execute(
			text("SELECT student_id FROM tbl_cp_resume_hashes WHERE hash = :hash"),
			{"hash": resume_hash},
		)
		existing = result.fetchone()
		already_existed = existing is not None
	except Exception as e:
		logger.warning(f"Hash pre-check failed: {e}")
		already_existed = False

	# STEP 4 — Save student core record
	try:
		salutation_id = None
		if parsed.salutation:
			sal_result = await lookup_service.find_salutation(db, parsed.salutation)
			if getattr(sal_result, "found", False):
				salutation_id = sal_result.salutation_id

		student_request = SaveStudentRequest(
			salutation_id=salutation_id,
			first_name=parsed.first_name,
			middle_name=parsed.middle_name,
			last_name=parsed.last_name,
			email=parsed.email,
			alt_email=parsed.alt_email,
			contact_number=parsed.contact_number,
			alt_contact_number=parsed.alt_contact_number,
			linkedin_url=parsed.linkedin_url,
			github_url=parsed.github_url,
			portfolio_url=parsed.portfolio_url,
			date_of_birth=parsed.date_of_birth,
			current_city=parsed.current_city,
			gender=parsed.gender,
		)
		student_result = await save_service.save_student(db, student_request)
		student_id = student_result.student_id
	except Exception as e:
		logger.error(f"Save-confirmed student save failed: {e}")
		raise ValueError(f"Failed to save student record: {e}")

	# STEP 5 — Save school records
	try:
		for school_item in parsed.school:
			if not school_item.standard:
				continue
			try:
				await save_service.save_school(
					db,
					SaveSchoolRequest(
						student_id=student_id,
						standard=school_item.standard,
						board=school_item.board,
						school_name=school_item.school_name,
						percentage=school_item.percentage,
						passing_year=school_item.passing_year,
					),
				)
				summary["schools_saved"] += 1
			except Exception as e:
				logger.warning(f"Failed to save school: {e}")
				warnings.append(f"School save failed: {e}")
	except Exception as e:
		logger.warning(f"Save-confirmed step 5 warning: {e}")

	# STEP 6 — Save college education
	try:
		for edu_item in parsed.education:
			if not edu_item.college_name or not edu_item.course_name:
				continue
			try:
				college_result = await lookup_service.find_or_create_college(db, edu_item.college_name)
				course_result = await lookup_service.find_or_create_course(
					db,
					edu_item.course_name,
					edu_item.specialization_name or "General",
				)
				await save_service.save_education(
					db,
					SaveEducationRequest(
						student_id=student_id,
						college_id=college_result.college_id,
						course_id=course_result.course_id,
						start_year=edu_item.start_year,
						end_year=edu_item.end_year,
						cgpa=edu_item.cgpa,
						percentage=edu_item.percentage,
					),
				)
				summary["educations_saved"] += 1
			except Exception as e:
				logger.warning(f"Failed to save education: {e}")
				warnings.append(f"Education save failed: {e}")
	except Exception as e:
		logger.warning(f"Save-confirmed step 6 warning: {e}")

	# STEP 7 — Save work experience
	workexp_map = {}
	try:
		for exp_item in parsed.workexp:
			if not exp_item.company_name:
				continue
			try:
				result = await save_service.save_workexp(
					db,
					SaveWorkExpRequest(
						student_id=student_id,
						company_name=exp_item.company_name,
						company_location=exp_item.company_location,
						designation=exp_item.designation,
						employment_type=exp_item.employment_type,
						start_date=exp_item.start_date,
						end_date=exp_item.end_date,
						is_current=exp_item.is_current,
					),
				)
				workexp_map[exp_item.company_name] = result.workexp_id
				summary["workexps_saved"] += 1
			except Exception as e:
				logger.warning(f"Failed to save workexp: {e}")
				warnings.append(f"Work experience save failed: {e}")
	except Exception as e:
		logger.warning(f"Save-confirmed step 7 warning: {e}")

	# STEP 8 — Save projects + skills
	try:
		for proj_item in parsed.projects:
			if not proj_item.project_title:
				continue
			try:
				linked_workexp_id = None
				if proj_item.workexp_company_name:
					linked_workexp_id = workexp_map.get(proj_item.workexp_company_name)

				proj_result = await save_service.save_project(
					db,
					SaveProjectRequest(
						student_id=student_id,
						workexp_id=linked_workexp_id,
						project_title=proj_item.project_title,
						project_description=proj_item.project_description,
						achievements=proj_item.achievements,
						project_start_date=proj_item.project_start_date,
						project_end_date=proj_item.project_end_date,
					),
				)
				summary["projects_saved"] += 1

				for skill_name in proj_item.skills_used:
					if not skill_name:
						continue
					try:
						skill_result = await lookup_service.find_or_create_skill(db, skill_name, "Intermediate")
						await save_service.save_project_skill(db, proj_result.project_id, skill_result.skill_id)
					except Exception as e:
						logger.warning(f"Failed to save project skill: {e}")
						warnings.append(f"Project skill save failed: {e}")
			except Exception as e:
				logger.warning(f"Failed to save project: {e}")
				warnings.append(f"Project save failed: {e}")
	except Exception as e:
		logger.warning(f"Save-confirmed step 8 warning: {e}")

	# STEP 9 — Save student skills
	try:
		for skill_item in parsed.skills:
			if not skill_item.name:
				continue
			try:
				skill_result = await lookup_service.find_or_create_skill(
					db, skill_item.name, skill_item.complexity or "Intermediate"
				)
				await save_service.save_student_skill(db, student_id, skill_result.skill_id)
				summary["skills_saved"] += 1
			except Exception as e:
				logger.warning(f"Failed to save student skill: {e}")
				warnings.append(f"Student skill save failed: {e}")
	except Exception as e:
		logger.warning(f"Save-confirmed step 9 warning: {e}")

	# STEP 10 — Save languages
	try:
		for lang_item in parsed.languages:
			if not lang_item.language_name:
				continue
			try:
				lang_result = await lookup_service.find_or_create_language(db, lang_item.language_name)
				await save_service.save_student_language(db, student_id, lang_result.language_id)
				summary["languages_saved"] += 1
			except Exception as e:
				logger.warning(f"Failed to save language: {e}")
				warnings.append(f"Language save failed: {e}")
	except Exception as e:
		logger.warning(f"Save-confirmed step 10 warning: {e}")

	# STEP 11 — Save certifications
	try:
		for cert_item in parsed.certifications:
			if not cert_item.certification_name or not cert_item.issuing_organization:
				continue
			try:
				cert_result = await lookup_service.find_or_create_certification(
					db,
					cert_item.certification_name,
					cert_item.issuing_organization,
					cert_item.certification_type or "General",
					cert_item.is_lifetime,
				)
				await save_service.save_student_certification(
					db,
					{
						"student_id": student_id,
						"certification_id": cert_result.certification_id,
						"issue_date": cert_item.issue_date,
						"expiry_date": cert_item.expiry_date,
						"certificate_url": cert_item.certificate_url,
						"credential_id": cert_item.credential_id,
					},
				)
				summary["certifications_saved"] += 1
			except Exception as e:
				logger.warning(f"Failed to save certification: {e}")
				warnings.append(f"Certification save failed: {e}")
	except Exception as e:
		logger.warning(f"Save-confirmed step 11 warning: {e}")

	# STEP 12 — Save interests
	try:
		for interest_item in parsed.interests:
			if not interest_item.name:
				continue
			try:
				interest_result = await lookup_service.find_or_create_interest(db, interest_item.name)
				await save_service.save_student_interest(db, student_id, interest_result.interest_id)
				summary["interests_saved"] += 1
			except Exception as e:
				logger.warning(f"Failed to save interest: {e}")
				warnings.append(f"Interest save failed: {e}")
	except Exception as e:
		logger.warning(f"Save-confirmed step 12 warning: {e}")

	# STEP 13 — Save addresses
	try:
		for addr_item in parsed.addresses:
			if not addr_item.address_line_1 or not addr_item.pincode:
				continue
			try:
				pincode_result = await lookup_service.find_pincode(db, addr_item.pincode)
				if not getattr(pincode_result, "found", False):
					warnings.append(f"Pincode {addr_item.pincode} not found. Address skipped.")
					continue

				await save_service.save_address(
					db,
					SaveAddressRequest(
						student_id=student_id,
						address_line_1=addr_item.address_line_1,
						address_line_2=addr_item.address_line_2,
						landmark=addr_item.landmark,
						pincode_id=pincode_result.pincode_id,
						address_type=addr_item.address_type or "current",
					),
				)
				summary["addresses_saved"] += 1
			except Exception as e:
				logger.warning(f"Failed to save address: {e}")
				warnings.append(f"Address save failed: {e}")
	except Exception as e:
		logger.warning(f"Save-confirmed step 13 warning: {e}")

	# STEP 14 — Store resume hash
	try:
		await db.execute(
			text("INSERT INTO tbl_cp_resume_hashes (hash, student_id) VALUES (:hash, :student_id)"),
			{"hash": resume_hash, "student_id": student_id},
		)
		await db.commit()
	except Exception as e:
		logger.warning(f"Resume hash storage failed: {e}")
		warnings.append(f"Resume hash storage failed: {e}")

	return {
		"student_id": student_id,
		"resume_hash": resume_hash,
		"already_existed": already_existed,
		"summary": summary,
		"warnings": warnings,
	}


# ---------------------------------------------------------------------------
# Bulk processing
# ---------------------------------------------------------------------------
async def process_bulk_resumes(
    batch_id: str,
    files_data: list
):
    """
    Processes multiple resume files one by one in background.
    Updates batch tracking status after each file.
    
    Parameters:
        batch_id: the batch ID created by create_batch()
        files_data: list of dicts with keys:
            - filename: str
            - file_bytes: bytes
            - extension: str (.pdf or .docx)
    """
    from utils.bulk_tracker import update_file_status
    from utils.quality_score import calculate_resume_quality
    from utils.hash_utils import compute_resume_hash
    from utils.cache_utils import save_to_cache, load_from_cache
    from services.extract_service import (
        extract_text_from_pdf,
        extract_text_from_docx
    )
    from services.llm_service import parse_resume_text
    
    logger.info(f"[BULK] Starting batch {batch_id[:8]}...")
    logger.info(f"[BULK] Total files: {len(files_data)}")
    print(f"[BULK] Starting batch {batch_id[:8]}...")
    print(f"[BULK] Total files: {len(files_data)}")
    
    for i, file_info in enumerate(files_data):
        filename = file_info["filename"]
        file_bytes = file_info["file_bytes"]
        extension = file_info["extension"]
        
        logger.info(f"[BULK] Processing file {i+1}/{len(files_data)}: {filename}")
        print(f"[BULK] Processing file {i+1}/{len(files_data)}: {filename}")
        
        # Mark as processing
        update_file_status(batch_id, filename, "processing")
        
        try:
            # Step 1: Extract text
            if extension == ".pdf":
                extract_result = await extract_text_from_pdf(file_bytes)
            elif extension == ".docx":
                extract_result = await extract_text_from_docx(file_bytes)
            else:
                raise ValueError(f"Unsupported file type: {extension}")
            
            resume_text = extract_result["text"]
            
            # Step 2: Check duplicate
            resume_hash = compute_resume_hash(resume_text)
            cached = load_from_cache(resume_hash)
            
            if cached:
                logger.info(f"[BULK] Cache hit for {filename} - skipping LLM")
                print(f"[BULK] Cache hit for {filename} - skipping LLM")
                parsed_dict = cached["parsed"]
                already_exists = True
            else:
                # Step 3: Parse with LLM
                logger.info(f"[BULK] Parsing {filename} with LLM...")
                print(f"[BULK] Parsing {filename} with LLM...")
                parsed_result = await parse_resume_text(resume_text)
                parsed_dict = parsed_result.model_dump()
                already_exists = False
            
            # Step 4: Calculate quality
            quality = calculate_resume_quality(parsed_dict)
            
            # Step 5: Save to cache (if not already cached)
            if not cached:
                cache_data = {
                    "resume_hash": resume_hash,
                    "already_exists": already_exists,
                    "parsed": parsed_dict,
                    "quality": quality
                }
                save_to_cache(resume_hash, cache_data)
            
            # Update tracker as complete
            update_file_status(
                batch_id=batch_id,
                filename=filename,
                status="complete",
                resume_hash=resume_hash,
                student_name=f"{parsed_dict.get('first_name', '')} {parsed_dict.get('last_name', '')}".strip(),
                email=parsed_dict.get("email", ""),
                quality_score=quality["score"]
            )
            
            logger.info(f"[BULK] ✓ {filename} done - Score: {quality['score']}/100")
            print(f"[BULK] ✓ {filename} done - Score: {quality['score']}/100")
            
        except Exception as e:
            error_msg = str(e)[:200]
            logger.error(f"[BULK] ✗ {filename} failed: {error_msg}")
            print(f"[BULK] ✗ {filename} failed: {error_msg}")
            update_file_status(
                batch_id=batch_id,
                filename=filename,
                status="failed",
                error=error_msg
            )
        
        # Small delay between files to avoid LLM rate limits
        if i < len(files_data) - 1:
            logger.info(f"[BULK] Waiting 3s before next file...")
            print(f"[BULK] Waiting 3s before next file...")
            await asyncio.sleep(3)
    
    logger.info(f"[BULK] Batch {batch_id[:8]}... finished processing all files")
    print(f"[BULK] Batch {batch_id[:8]}... finished processing all files")

