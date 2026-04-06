===================================================
SECTION 1: PROJECT SUMMARY
===================================================

This project is an asynchronous FastAPI resume parsing backend that extracts text from PDF/DOCX resumes, sends the text to an LLM extraction pipeline, validates and normalizes the structured output, and writes the result into a MySQL campus database schema (campus5). It solves the manual data-entry problem for student profile onboarding by converting unstructured resume content into normalized records across student, education, work experience, projects, skills, languages, certifications, interests, and addresses. It is used by the ArtisetCampus website (as API client) and operations/users who upload resumes, preview parsed output, confirm edits, and then persist data to database tables.

===================================================
SECTION 2: TECHNOLOGY STACK
===================================================

Web Framework

| Technology | Version | Purpose | Why This Was Chosen |
|---|---|---|---|
| fastapi | >=0.100.0 | API framework for all endpoints and request handling. | Native async support, strong typing, and automatic OpenAPI docs are a good fit for structured parsing APIs. |
| uvicorn[standard] | >=0.25.0 | ASGI server to run the FastAPI app. | Standard production/dev runtime for FastAPI with good performance and simple startup. |

Database

| Technology | Version | Purpose | Why This Was Chosen |
|---|---|---|---|
| sqlalchemy | >=2.0.0 | ORM base classes and SQL execution for async database operations. | Allows both model definitions and direct SQL text queries in one stack. |
| aiomysql | >=0.2.0 | Async MySQL driver used by SQLAlchemy async engine (mysql+aiomysql). | Required for non-blocking DB I/O in asyncio routes/services. |
| pymysql | >=1.1.0 | MySQL client dependency commonly used alongside MySQL ecosystems. | Compatibility/fallback dependency for MySQL tooling and environments. |

AI / LLM

| Technology | Version | Purpose | Why This Was Chosen |
|---|---|---|---|
| httpx | >=0.25.0 | Async HTTP client used for OpenRouter chat/completions calls. | Clean async API, timeout controls, and straightforward JSON request/response handling. |

File Processing

| Technology | Version | Purpose | Why This Was Chosen |
|---|---|---|---|
| PyMuPDF | >=1.20.0 | Extracts text from PDF resumes. | Fast and reliable direct PDF text extraction through fitz. |
| python-docx | >=1.0.0 | Extracts text from DOCX paragraphs and tables. | Mature DOCX parser that covers common resume document structures. |

Validation

| Technology | Version | Purpose | Why This Was Chosen |
|---|---|---|---|
| pydantic | >=2.5.0 | Request/response/data model validation and type coercion. | Strong schema validation and validators for cleaning LLM outputs (dates/years/floats). |
| pydantic-settings | >=2.0.0 | Environment-driven settings management. | Simple settings class pattern with typed env loading from .env. |

Utilities

| Technology | Version | Purpose | Why This Was Chosen |
|---|---|---|---|
| python-dotenv | >=1.0.0 | Loads environment variables from .env files. | Standard approach for local/dev configuration portability. |
| python-multipart | >=0.0.6 | Supports multipart/form-data file uploads in FastAPI. | Required dependency for UploadFile endpoints. |
| cryptography | >=40.0.0 | Security/crypto support dependency in runtime environment. | Common required dependency in stacks that include secure database/network libs. |

===================================================
SECTION 3: SYSTEM ARCHITECTURE
===================================================

Client (ArtisetCampus website)
        -> HTTP requests
FastAPI Application (this project)
        -> OpenRouter API (Gemini-named helper exists but is deprecated in code)
        -> MySQL Database (campus5)
        -> File Processing (PyMuPDF + python-docx)

Client layer: The web client uploads resume files and calls parsing/saving endpoints. It can use normal request-response routes or SSE progress streaming for longer parsing tasks.

API layer (FastAPI): The app validates input, routes requests to orchestrator/service modules, computes resume hashes, performs duplicate checks, and coordinates extraction, LLM parsing, quality scoring, caching, and persistence.

LLM layer: The code calls OpenRouter chat/completions asynchronously with a 2-pass extraction strategy (extract + gap check). A function named _call_gemini_api exists but only redirects to the OpenRouter call and is marked deprecated.

Database layer: MySQL is accessed via SQLAlchemy async sessions and text queries for lookup, insert, and duplicate checks. The app creates tbl_cp_resume_hashes on startup if missing and writes parsed entities into multiple normalized tables.

File processing layer: PDF text extraction uses PyMuPDF and DOCX extraction uses python-docx (paragraphs + tables). Unsupported file types are rejected before extraction.

===================================================
SECTION 4: ALL API ENDPOINTS
===================================================

Extract endpoints (/extract/*)

| Method | URL | Purpose | Request | Response |
|---|---|---|---|---|
| POST | /extract/pdf-to-text | Extract text from PDF resume. | multipart/form-data with file (.pdf), size <= MAX_FILE_SIZE_MB | SuccessResponse with text, page_count, char_count; error on invalid type/size/extraction |
| POST | /extract/docx-to-text | Extract text from DOCX resume. | multipart/form-data with file (.docx), size <= MAX_FILE_SIZE_MB | SuccessResponse with text, paragraph_count, char_count; error on invalid type/size/extraction |

Parse endpoints (/parse/*)

| Method | URL | Purpose | Request | Response |
|---|---|---|---|---|
| POST | /parse/resume | Parse raw resume text using 2-pass LLM. | JSON ParseResumeRequest { resume_text } (min 100 chars) | SuccessResponse with parsed (ParsedResume) + resume_hash |

Lookup endpoints (/lookup/*)

| Method | URL | Purpose | Request | Response |
|---|---|---|---|---|
| POST | /lookup/skill | Find-or-create skill master record. | LookupSkillRequest { name, complexity? } | LookupSkillResponse wrapped in SuccessResponse |
| POST | /lookup/language | Find-or-create language master record. | LookupLanguageRequest { language_name } | LookupLanguageResponse wrapped in SuccessResponse |
| POST | /lookup/interest | Find-or-create interest master record. | LookupInterestRequest { name } | LookupInterestResponse wrapped in SuccessResponse |
| POST | /lookup/certification | Find-or-create certification master record. | LookupCertificationRequest { certification_name, issuing_organization, certification_type?, is_lifetime? } | LookupCertificationResponse wrapped in SuccessResponse |
| POST | /lookup/college | Find-or-create college master record. | LookupCollegeRequest { college_name } | LookupCollegeResponse wrapped in SuccessResponse |
| POST | /lookup/course | Find-or-create course master record. | LookupCourseRequest { course_name, specialization_name? } | LookupCourseResponse wrapped in SuccessResponse |
| POST | /lookup/salutation | Read-only salutation lookup. | LookupSalutationRequest { value } | LookupSalutationResponse wrapped in SuccessResponse |
| POST | /lookup/pincode | Read-only pincode lookup. | LookupPincodeRequest { pincode } | LookupPincodeResponse wrapped in SuccessResponse |

Save endpoints (/save/*)

| Method | URL | Purpose | Request | Response |
|---|---|---|---|---|
| POST | /save/student | Save student core row. | SaveStudentRequest | SaveStudentResponse wrapped in SuccessResponse |
| POST | /save/school | Save school row. | SaveSchoolRequest | school_id in SuccessResponse |
| POST | /save/education | Save college education row. | SaveEducationRequest | edu_id in SuccessResponse |
| POST | /save/workexp | Save work experience row. | SaveWorkExpRequest | SaveWorkExpResponse wrapped in SuccessResponse |
| POST | /save/project | Save project row. | SaveProjectRequest | SaveProjectResponse wrapped in SuccessResponse |
| POST | /save/project-skill | Save project-skill relationship. | SaveProjectSkillRequest | already_exists in SuccessResponse |
| POST | /save/student-skill | Save student-skill relationship. | { student_id, skill_id } | already_exists in SuccessResponse |
| POST | /save/student-language | Save student-language relationship. | { student_id, language_id } | already_exists in SuccessResponse |
| POST | /save/student-interest | Save student-interest relationship. | { student_id, interest_id } | already_exists in SuccessResponse |
| POST | /save/student-certification | Save student-certification relationship. | { student_id, certification_id, issue_date?, expiry_date?, certificate_url?, credential_id? } | already_exists in SuccessResponse |
| POST | /save/address | Save student address row. | SaveAddressRequest | SaveAddressResponse wrapped in SuccessResponse |

Resume endpoints (/resume/*)

| Method | URL | Purpose | Request | Response |
|---|---|---|---|---|
| POST | /resume/upload | Full parse-and-save pipeline. | multipart/form-data with file (.pdf/.docx), size-limited | student_id, resume_hash, summary, warnings |
| POST | /resume/parse-preview | Parse only (no DB writes), with cache support. | multipart/form-data with file (.pdf/.docx), size-limited | resume_hash, already_exists, parsed, quality |
| POST | /resume/parse-with-progress | Streaming parse with SSE progress events. | multipart/form-data with file (.pdf/.docx) | text/event-stream with progress/complete/error events |
| GET | /resume/get-cached/{resume_hash} | Fetch cached parsed payload by hash. | Path param resume_hash | Cached data if found; 404 if missing |
| POST | /resume/save-confirmed | Persist confirmed/edited parsed payload. | SaveConfirmedRequest { resume_hash, parsed } | student_id, resume_hash, summary, warnings |
| GET | /resume/cache-status | Inspect cache count and hashes. | None | cached_count and cached_hashes |
| GET | /resume/quality-score/{resume_hash} | Return quality score from cached parsed data. | Path param resume_hash | quality score object; 404 if cache missing |
| POST | /resume/bulk-upload | Start background batch parse (max 10 files). | multipart/form-data files[] (.pdf/.docx) | batch_id and status URL (202 Accepted) |
| GET | /resume/bulk-status/{batch_id} | Get batch processing progress and per-file status. | Path param batch_id | progress, counts, and file-level statuses |

Health endpoint (/health)

| Method | URL | Purpose | Request | Response |
|---|---|---|---|---|
| GET | /health | Runtime health check for DB, OpenRouter config, cache, extraction libs, stats, uptime. | None | Component status object with overall status |

Additional non-router app endpoints in main.py

| Method | URL | Purpose | Request | Response |
|---|---|---|---|---|
| GET | / | Root metadata endpoint. | None | API name/version/docs URLs |
| GET | /favicon.ico | Suppress favicon errors. | None | HTTP 204 |

===================================================
SECTION 5: DATABASE TABLES USED
===================================================

Tables the parser WRITES to (creates data)

- tbl_cp_student: core student profile and contact fields.
- tbl_cp_student_school: 10th/12th school education entries.
- tbl_cp_student_education: college/university education rows.
- tbl_cp_student_workexp: work experience entries.
- tbl_cp_studentprojects: projects linked to student (and optionally workexp).
- tbl_cp_m2m_studentproject_skill: project-to-skill mappings.
- tbl_cp_m2m_std_skill: student-to-skill mappings.
- tbl_cp_m2m_std_lng: student-to-language mappings.
- tbl_cp_m2m_std_interest: student-to-interest mappings.
- tbl_cp_m2m_student_certification: student-to-certification mappings and metadata.
- tbl_cp_student_address: student addresses linked by pincode_id.
- tbl_cp_resume_hashes: resume hash to student mapping for duplicate detection.
- tbl_cp_mskills: may insert new master skills during lookup find-or-create.
- tbl_cp_mlanguages: may insert new master languages.
- tbl_cp_minterests: may insert new master interests.
- tbl_cp_mcertifications: may insert new master certifications.
- tbl_cp_mcolleges: may insert new master colleges.
- tbl_cp_mcourses: may insert new master courses/specializations.

Tables the parser READS from (lookup only)

- tbl_cp_msalutation: read-only salutation ID lookup.
- tbl_cp_mpincodes: read-only pincode ID lookup.
- tbl_cp_mskills: existence checks before potential insert.
- tbl_cp_mlanguages: existence checks; also fetches General language_id for new skills.
- tbl_cp_minterests: existence checks before potential insert.
- tbl_cp_mcertifications: existence checks before potential insert.
- tbl_cp_mcolleges: existence checks before potential insert.
- tbl_cp_mcourses: existence checks before potential insert.
- tbl_cp_student: existence check by email during save_student.
- tbl_cp_m2m_studentproject_skill: duplicate mapping checks.
- tbl_cp_m2m_std_skill: duplicate mapping checks.
- tbl_cp_m2m_std_lng: duplicate mapping checks.
- tbl_cp_m2m_std_interest: duplicate mapping checks.
- tbl_cp_m2m_student_certification: duplicate mapping checks.
- tbl_cp_resume_hashes: duplicate resume checks and pre-check in save-confirmed.

Tables created by the parser on startup

- tbl_cp_resume_hashes: created via CREATE TABLE IF NOT EXISTS in app lifespan startup.

===================================================
SECTION 6: HOW A RESUME IS PROCESSED
===================================================

Step 1: File validation and type check (.pdf/.docx only, max size from MAX_FILE_SIZE_MB).
Timing in code: not separately timed at router level.

Step 2: Text extraction (PyMuPDF for PDF, python-docx for DOCX).
Timing in code: explicitly timed and printed as Text extraction.

Step 3: SHA-256 hash generation from extracted text.
Timing in code: included in Hash check timer block.

Step 4: Duplicate check against tbl_cp_resume_hashes.
Timing in code: explicitly timed and printed as Hash check.

Step 5: LLM Pass 1 extraction (full schema extraction).
Timing in code: pass1_elapsed tracked in llm_service.parse_resume_text.

Step 6: LLM Pass 2 gap-check (find missed/wrong values).
Timing in code: pass2_elapsed tracked in llm_service.parse_resume_text.

Step 7: Merge pass outputs and normalize types (years/cgpa/skills_used).
Timing in code: no dedicated timer; included in LLM total.

Step 8: ParsedResume validation (Pydantic validation and coercion).
Timing in code: no dedicated timer.

Step 9: Save student core row (tbl_cp_student).
Timing in code: no per-step timer in orchestrator full pipeline.

Step 10: Save school rows (tbl_cp_student_school).
Timing in code: no per-step timer.

Step 11: Save college education rows (with lookup/create college and course).
Timing in code: no per-step timer.

Step 12: Save work experience rows and build company->workexp map.
Timing in code: no per-step timer.

Step 13: Save project rows and project-skill mappings.
Timing in code: no per-step timer.

Step 14: Save student skills, languages, certifications, interests, and addresses.
Timing in code: no per-step timer (all in separate blocks without duration logging).

Step 15: Store resume hash mapping and return summary/warnings response.
Timing in code: no dedicated step timer; overall pipeline total is printed.

Observed timing instrumentation from code:

- Full pipeline prints: Text extraction, Hash check, LLM Pass 1, LLM Pass 2, TOTAL.
- Preview pipeline prints: Text extraction, Hash check, LLM Pass 1, LLM Pass 2, Cache save, TOTAL.
- LLM service prints: Pass 1 elapsed, Pass 2 elapsed, and LLM total.

===================================================
SECTION 7: KEY DESIGN DECISIONS
===================================================

1. Why 2 LLM passes instead of 1
- The first pass extracts full structured JSON; the second pass re-reads source text plus pass1 output to fill gaps and correct misses.
- This is explicitly encoded in llm_service.parse_resume_text using SYSTEM_PROMPT_PASS1 and SYSTEM_PROMPT_PASS2 and then merged.
- The intended tradeoff is higher accuracy/completeness at the cost of higher latency.

2. Why file-based cache instead of database cache
- Cache is implemented in utils/cache_utils.py as JSON files under resume_cache and resume_cache/bulk.
- This avoids additional DB schema complexity for temporary preview/batch state and allows fast local retrieval by hash.
- It is simple to inspect and debug, but tied to local filesystem persistence.

3. Why COALESCE(MAX(id),0)+1 instead of AUTO_INCREMENT
- Many inserts in save_service.py and lookup_service.py manually allocate business IDs (student_id, skill_id, college_id, etc.) via COALESCE(MAX(...),0)+1.
- This suggests compatibility with an existing campus schema where row_id auto-increments but domain IDs are managed separately.
- Tradeoff: simple integration with legacy IDs, but potential race-condition risk under heavy concurrent inserts.

4. Why asyncio.to_thread() is used for Gemini calls
- In the current codebase, asyncio.to_thread() is not used for LLM calls.
- Current implementation uses native async HTTP calls via httpx.AsyncClient and asyncio.wait_for in llm_service.py.
- There is a deprecated _call_gemini_api function name, but it simply forwards to OpenRouter async call.

5. Why lookup endpoints use find-or-create pattern
- lookup_service.py follows read-then-create behavior for skills, languages, interests, certifications, colleges, and courses.
- This allows parser pipelines to continue even when master records are missing, reducing manual pre-configuration requirements.
- Each function also re-fetches on insert error to handle duplicate races gracefully and return existing IDs.

===================================================
SECTION 8: KNOWN LIMITATIONS
===================================================

- Unsupported file types: only PDF and DOCX are accepted; scanned/image-only resumes are not OCR-processed and can fail extraction.
- Very long resumes: LLM request uses max_tokens=4096 and timeout=120s per call; long or complex resumes can timeout or truncate quality.
- If Gemini is down: current pipeline does not call Gemini directly; it calls OpenRouter. If OpenRouter/API key/network fails, parsing endpoints return errors and cannot continue.
- If database is down: lookup/save/full-pipeline endpoints fail; /health reports degraded status with DB disconnected details.
- Current performance benchmarks in code comments/logging:
  - SSE status text indicates AI analysis can take roughly 60-90 seconds.
  - Bulk endpoint notes 10-15 seconds per file (background processing note).
  - Full/preview pipelines log extraction/hash/LLM/total timings, but no persisted benchmark report exists in repo.
- ID generation concurrency: COALESCE(MAX(id),0)+1 can collide under parallel writes without transactional/locking safeguards.
- Cache durability/scope: cache is local filesystem; not distributed/shared across multiple app instances.

===================================================
SECTION 9: DEPLOYMENT REQUIREMENTS
===================================================

Infrastructure

- Server profile (code-based practical minimum):
  - CPU: 2+ vCPU recommended (async API + PDF parsing + DB I/O + HTTP calls)
  - RAM: 4 GB minimum recommended
  - Storage: enough for app logs and resume_cache files (variable with usage)
- Required software:
  - Python 3.10+ (compatible with listed dependencies)
  - MySQL server reachable by configured DB_* values
- Required open ports:
  - API port: APP_PORT (default 8000)
  - MySQL port: DB_PORT (default 3306) from app host to DB host
  - Outbound HTTPS (443) to OpenRouter API

Environment Variables

From .env.example:

- OPENROUTER_API_KEY: required for parsing (without it LLM parsing fails).
- OPENROUTER_MODEL: optional (default exists in config.py: openai/gpt-3.5-turbo).
- DB_HOST: required for DB connectivity (default exists: localhost).
- DB_PORT: optional if using default 3306.
- DB_USER: required for DB auth (default exists: root).
- DB_PASSWORD: optional in code (empty default), but practically required for secured DBs.
- DB_NAME: optional if using default campus5.
- APP_ENV: optional (default development).
- APP_PORT: optional (default 8000).
- MAX_FILE_SIZE_MB: optional (default 10).
- ALLOWED_EXTENSIONS: optional (default pdf,docx).

External Services

- OpenRouter API (https://openrouter.ai/api/v1/chat/completions): used for LLM extraction.
  - If unavailable: parse endpoints fail; upload/preview pipelines that depend on parse fail.
- MySQL (campus5): used for lookup and persistence.
  - If unavailable: save/lookups/full pipeline fail; health endpoint reports degraded DB status.
- Local filesystem (resume_cache): used for cache and bulk tracker JSON files.
  - If unavailable/unwritable: preview/bulk cache behavior fails or degrades.

===================================================
SECTION 10: QUICK START GUIDE
===================================================

Prerequisites:
1. Install Python 3.10+.
2. Install and run MySQL; ensure database campus5 exists and schema tables referenced by code are present (except tbl_cp_resume_hashes, which is auto-created).
3. Ensure outbound internet access to OpenRouter.

Setup:
1. Clone/copy the project to a machine.
2. Create and activate virtual environment.
3. Install dependencies: pip install -r requirements.txt.
4. Create .env from .env.example and fill values, especially OPENROUTER_API_KEY and DB_*.
5. Confirm ALLOWED_EXTENSIONS and MAX_FILE_SIZE_MB meet your use case.

Running:
1. Start API server: python -m uvicorn main:app --host 0.0.0.0 --port 8000.
2. Verify startup logs show tbl_cp_resume_hashes ensured.
3. Open API docs at /docs and check /health endpoint.

Testing:
1. Test extraction only with /extract/pdf-to-text or /extract/docx-to-text.
2. Test parse-only text flow with /parse/resume (raw text JSON).
3. Test real upload preview with /resume/parse-preview; verify parsed + quality output.
4. Test full save pipeline with /resume/upload or two-step /resume/parse-preview then /resume/save-confirmed.
5. Test batch flow with /resume/bulk-upload and poll /resume/bulk-status/{batch_id}.
