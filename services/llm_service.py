import json
import re
import logging
import time
import asyncio
import httpx
from config import get_settings
from schemas.parse_schema import ParsedResume

# Setup OpenRouter client at module level
settings = get_settings()
logger = logging.getLogger(__name__)

# OpenRouter API configuration
OPENROUTER_API_KEY = settings.openrouter_api_key
OPENROUTER_MODEL = settings.openrouter_model
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"

SYSTEM_PROMPT_PASS1 = """
You are a precise resume data extraction engine.
Your only job is to read the resume text and return a single JSON object.
No explanations. No markdown. No extra text. Only raw JSON.

CRITICAL RULES:
1. Every field listed in the schema MUST appear in your output — even if the value is null.
2. Never skip a field. Never add extra fields not in the schema.
3. Read EVERY line of the resume. Do not stop early.
4. If a value is not found, return null — not empty string "", not "N/A", not "Not Found", not "Unknown".
5. Return arrays even when there is only one item. Never return a single object where array is expected.
6. Dates must follow this format exactly: YYYY-MM-DD. If only month+year known: YYYY-MM-01. If only year known: YYYY-01-01.
7. For boolean fields: return true or false only — never strings like "true" or "yes".
8. Use exact field names as given in schema — same spelling, same underscores, same case.
9. NEVER invent or guess values for contact_number, alt_contact_number,
email, alt_email, linkedin_url, github_url, portfolio_url, date_of_birth,
or credential_id. If these are not clearly and explicitly written in the
resume text, return null. Do NOT construct or guess these values from
patterns or names.
10. For interests[] — this field is ONLY for career domain areas like
"Machine Learning", "Web Development", "Data Science", "Cybersecurity",
"Cloud Computing". If the resume has a section called "INTERESTS" or
"HOBBIES" with values like "Badminton", "Music", "Travelling", "Reading",
"Cricket" — these are hobbies, NOT career interests. Do NOT put hobbies
into interests[]. Instead return interests[] based only on:
- Sections explicitly titled "Areas of Interest" or "Career Interests"
  or "Domain Interests"
- Inference from projects and skills (3+ ML projects = "Machine Learning")
If no career domain interests can be found or inferred, return interests
as an empty array [].
11. For passing_year in school[] — if the year seems logically
impossible (example: 10th passing year is AFTER or SAME as 12th passing
year), return null for that passing_year instead of the impossible value.
A student completes 10th before 12th. 10th year must always be less than
12th year. If the resume has a typo that violates this, return null.
12.For designation in workexp[] — only return a value if the
designation is explicitly written directly under or next to that specific
company entry. Do NOT infer or carry over designation from the resume
summary paragraph or profile bio section. If designation is not directly
written for a company, return null.

INFERENCE RULES (apply when data is not directly written):
- employment_type: if designation contains "intern" or "internship" anywhere → "Internship".
  If job duration is under 6 months and no type is given → "Internship".
  If contract-based wording is used → "Contract".
  If no clue at all → "Full-Time".
- is_current in workexp: if end_date is missing OR resume says "Present" or "Current" → true. end_date = null.
- is_lifetime in certifications: if no expiry date mentioned → true.
- address_type: if only one address found → "current". If two addresses → identify which is current and which is permanent.
- salutation: infer ONLY if clearly written in resume (Dr., Prof., Mr., Ms., Mrs.). If not clear → null.
- workexp_company_name in projects: if a project is listed under a company name in the work experience section, set workexp_company_name to that exact company name.
- complexity in skills: "proficient"/"expert"/"advanced"/"strong" in resume → "Expert". "familiar"/"basic"/"learning"/"beginner" → "Beginner". Skill just listed with no qualifier → "Intermediate".
- interests: IMPORTANT — this field stores career domain interests like "Web Development", "Data Science", "Machine Learning", "Cybersecurity", "Cloud Computing", "Mobile Development". NOT hobbies.
  Extract from sections titled "Areas of Interest", "Career Interests", "Domain Interests".
  Also infer: if student has 3+ ML-related projects AND ML skills → add "Machine Learning" with is_inferred=true.
  If student has web projects and frameworks like React/Angular → add "Web Development" with is_inferred=true.
  Mark directly stated interests with is_inferred=false.

NAME SPLITTING:
- first_name: the first word of the full name.
- middle_name: middle word(s) if full name has 3 or more words. Otherwise null.
- last_name: the last word of the full name. If full name is only one word → first_name = that word, last_name = null.
"""

SYSTEM_PROMPT_PASS2 = """
You are a resume data quality checker.
You will receive the original resume text AND a JSON object already extracted from it.
Your job: find anything MISSED or WRONG in the extracted JSON.
Return ONLY the corrected complete JSON. Same schema. No explanations. No markdown. Only raw JSON.

WHAT TO CHECK CAREFULLY:
1. Skills: scan every line — project descriptions, work experience bullets, certifications section. Any tool/technology/framework/library not in skills[] → add it.
2. Projects: any project missing or has null project_description? Fill it from resume text.
3. Certifications: any cert mentioned in passing anywhere in the resume not in certifications[]? Add it.
4. Languages: any spoken or written language missing from languages[]? Add it.
5. Interests (career domains): any domain area missing? Remember — not hobbies, but career domains.
6. Contact info: any phone number, email, URL, LinkedIn, GitHub, portfolio link missed?
7. Dates: are any dates in wrong format? Must be YYYY-MM-DD. Fix them.
8. Null fields: go through every null field and check if the value is actually present in the resume.
9. skills_used in each project: list every tool/technology mentioned in that specific project description.
10. School entries: is 10th AND 12th both captured if mentioned? Check.
11. Address: is the pincode, city, state, country captured if mentioned?

RULES:
- Return the COMPLETE JSON — not just the changes.
- Do not remove any field that already has a correct value.
- Only fix what is wrong or add what is missing.
- Keep all field names exactly the same as given.
"""

JSON_SCHEMA_TEMPLATE = """{
  "salutation": null,
  "first_name": null,
  "middle_name": null,
  "last_name": null,
  "email": null,
  "alt_email": null,
  "contact_number": null,
  "alt_contact_number": null,
  "linkedin_url": null,
  "github_url": null,
  "portfolio_url": null,
  "date_of_birth": null,
  "current_city": null,
  "gender": null,
  "school": [
    {
      "standard": null,
      "board": null,
      "school_name": null,
      "percentage": null,
      "passing_year": null
    }
  ],
  "education": [
    {
      "college_name": null,
      "course_name": null,
      "specialization_name": null,
      "start_year": null,
      "end_year": null,
      "cgpa": null,
      "percentage": null
    }
  ],
  "workexp": [
    {
      "company_name": null,
      "company_location": null,
      "designation": null,
      "employment_type": null,
      "start_date": null,
      "end_date": null,
      "is_current": null
    }
  ],
  "projects": [
    {
      "project_title": null,
      "project_description": null,
      "achievements": null,
      "project_start_date": null,
      "project_end_date": null,
      "workexp_company_name": null,
      "skills_used": []
    }
  ],
  "skills": [
    {
      "name": null,
      "complexity": null
    }
  ],
  "languages": [
    {
      "language_name": null
    }
  ],
  "certifications": [
    {
      "certification_name": null,
      "issuing_organization": null,
      "certification_type": null,
      "issue_date": null,
      "expiry_date": null,
      "is_lifetime": null,
      "certificate_url": null,
      "credential_id": null
    }
  ],
  "interests": [
    {
      "name": null,
      "is_inferred": null
    }
  ],
  "addresses": [
    {
      "address_line_1": null,
      "address_line_2": null,
      "landmark": null,
      "pincode": null,
      "city_name": null,
      "state_name": null,
      "country_name": null,
      "address_type": null
    }
  ]
}"""


def clean_and_parse_json(raw_text: str) -> dict:
    """
    Strips markdown fences and parses JSON from LLM response.
    OpenRouter sometimes adds ```json blocks even with JSON content-type.
    """
    clean = raw_text.strip()
    clean = re.sub(r'^```json\s*', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'^```\s*', '', clean)
    clean = re.sub(r'\s*```$', '', clean)
    try:
        return json.loads(clean.strip())
    except json.JSONDecodeError as e:
        # Try to find JSON object in the text
        start = clean.find('{')
        end = clean.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(clean[start:end+1])
            except:
                pass
        raise ValueError(
            f"OpenRouter response is not valid JSON: {e}. "
            f"Raw text preview: {raw_text[:300]}"
        )


async def _call_openrouter_api(full_prompt: str) -> str:
    """
    Async call to OpenRouter API.
    Uses httpx.AsyncClient for non-blocking HTTP requests.
    Returns raw text response from the LLM.
    """
    print(f"[OPENROUTER] Starting API call...")
    print(f"[OPENROUTER] Prompt length: {len(full_prompt)} chars")
    
    start = time.time()
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Resume Parser"
    }
    
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "user", "content": full_prompt}
        ],
        "temperature": 0.0,
        "max_tokens": 4096
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OPENROUTER_API_BASE}/chat/completions",
                headers=headers,
                json=payload
            )
            
            elapsed = time.time() - start
            
            if response.status_code != 200:
                error_text = response.text
                print(f"[OPENROUTER] ERROR after {elapsed:.2f}s: Status {response.status_code}")
                print(f"[OPENROUTER] Response: {error_text}")
                logger.error(f"[OPENROUTER] API Error {response.status_code}: {error_text}")
                raise ValueError(f"OpenRouter API error: {response.status_code} - {error_text}")
            
            result = response.json()
            message_content = result["choices"][0]["message"]["content"]
            
            print(f"[OPENROUTER] Got response in {elapsed:.2f}s")
            print(f"[OPENROUTER] Response length: {len(message_content)} chars")
            
            return message_content
        
    except asyncio.TimeoutError:
        elapsed = time.time() - start
        print(f"[OPENROUTER] TIMEOUT after {elapsed:.2f}s")
        logger.error(f"[OPENROUTER] Timeout after {elapsed:.2f}s")
        raise
    except Exception as e:
        elapsed = time.time() - start
        print(f"[OPENROUTER] ERROR after {elapsed:.2f}s: {str(e)}")
        logger.error(f"[OPENROUTER] API error: {e}")
        raise


async def _call_gemini_api(full_prompt: str) -> str:
    """
    DEPRECATED - Use _call_openrouter_api instead.
    This function is kept for backward compatibility but redirects to OpenRouter.
    """
    return await _call_openrouter_api(full_prompt)


async def call_llm(system_prompt: str, user_message: str) -> dict:
    """
    Calls OpenRouter API asynchronously.
    No blocking calls - fully async/await compatible with FastAPI.
    Includes 120-second timeout protection.
    """
    
    full_prompt = f"""{system_prompt}

=== YOUR TASK ===
{user_message}

REMINDER: Return ONLY valid JSON. No explanation. 
No markdown. No extra text. Pure JSON only."""

    print(f"[OPENROUTER] Calling OpenRouter API (async)...")
    start_time = time.time()
    
    try:
        # True async call - no blocking
        raw_text = await asyncio.wait_for(
            _call_openrouter_api(full_prompt),
            timeout=120.0  # 2 minute timeout
        )
        
        elapsed = time.time() - start_time
        print(f"[OPENROUTER] Response received in {elapsed:.2f}s")
        
        result = clean_and_parse_json(raw_text)
        print(f"[OPENROUTER] JSON parsed successfully")
        return result
        
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        print(f"[OPENROUTER] TIMEOUT after {elapsed:.2f}s")
        logger.error(f"[OPENROUTER] Timeout after {elapsed:.2f}s")
        raise ValueError(
            "OpenRouter API timed out after 2 minutes. "
            "Check your API key and internet connection."
        )
        
    except Exception as e:
        elapsed = time.time() - start_time
        error_str = str(e)
        
        print(f"[OPENROUTER] ERROR after {elapsed:.2f}s: {error_str}")
        logger.error(f"[OPENROUTER] API error: {e}")
        raise


def merge_pass1_and_pass2(pass1: dict, pass2: dict) -> dict:
    """
    Merges two LLM pass results.
    For scalars: use pass2 if not None, else pass1.
    For arrays: use whichever is longer.
    """
    merged = dict(pass1)
    for key in pass2:
        if isinstance(pass2[key], list):
            p1_arr = pass1.get(key) or []
            p2_arr = pass2.get(key) or []
            merged[key] = p2_arr if len(p2_arr) >= len(p1_arr) else p1_arr
        else:
            merged[key] = pass2[key] if pass2[key] is not None else pass1.get(key)
    return merged


def normalize_merged(merged: dict) -> dict:
  """
  Normalizes certain LLM output fields to match Pydantic schema types.

  - Convert education[].cgpa from strings like '3.8/4.0' or '3.8' to float 3.8
  - Convert education[].start_year and end_year from date strings to int (extract year)
  - Convert projects[].skills_used entries that are objects to simple strings (skill names)
  - Convert school[].passing_year to int if provided as string/date
  """
  # Normalize passing_year in school entries to int (extract 4-digit year)
  for sch in merged.get("school", []):
    py = sch.get("passing_year")
    if isinstance(py, str):
      m = re.search(r"(\d{4})", py)
      if m:
        try:
          sch["passing_year"] = int(m.group(1))
        except Exception:
          sch["passing_year"] = None
      else:
        sch["passing_year"] = None

  # Normalize start_year and end_year in education entries (extract 4-digit year from dates)
  for edu in merged.get("education", []):
    if not isinstance(edu, dict):
      continue
    for year_field in ["start_year", "end_year"]:
      year_val = edu.get(year_field)
      if year_val is None:
        continue
      if isinstance(year_val, int):
        # Already an integer, leave it
        continue
      if isinstance(year_val, str):
        year_val = year_val.strip()
        if not year_val:
          edu[year_field] = None
          continue
        # Try to extract 4-digit year from date strings like "2026-01-01"
        m = re.search(r"(\d{4})", year_val)
        if m:
          try:
            edu[year_field] = int(m.group(1))
          except Exception as e:
            print(f"[WARNING] Failed to convert {year_field}={year_val}: {e}")
            edu[year_field] = None
        else:
          # Try direct int conversion
          try:
            edu[year_field] = int(year_val)
          except Exception:
            print(f"[WARNING] Could not extract year from {year_field}={year_val}")
            edu[year_field] = None
      else:
        # For any other type, try converting to string first then extracting year
        try:
          str_val = str(year_val).strip()
          m = re.search(r"(\d{4})", str_val)
          if m:
            edu[year_field] = int(m.group(1))
          else:
            edu[year_field] = None
        except Exception as e:
          print(f"[WARNING] Failed to process {year_field}={year_val} (type={type(year_val)}): {e}")
          edu[year_field] = None
    
    # Normalize CGPA
    cgpa = edu.get("cgpa")
    if isinstance(cgpa, str):
      # Try to extract the first float (handles '3.8/4.0', '3.8', '3.8 out of 4')
      m = re.search(r"(\d+(?:\.\d+)?)", cgpa)
      if m:
        try:
          edu["cgpa"] = float(m.group(1))
        except Exception:
          edu["cgpa"] = None

  # Normalize projects[].skills_used to be list[str]
  for proj in merged.get("projects", []):
    skills_used = proj.get("skills_used")
    if isinstance(skills_used, list):
      normalized = []
      for s in skills_used:
        if isinstance(s, str):
          normalized.append(s)
        elif isinstance(s, dict):
          # Common keys: 'name', 'skill', 'skill_name'
          name = s.get("name") or s.get("skill") or s.get("skill_name")
          if isinstance(name, str):
            normalized.append(name)
          else:
            # fallback: stringify the dict
            try:
              normalized.append(str(name))
            except Exception:
              continue
        else:
          # fallback for unexpected types
          try:
            normalized.append(str(s))
          except Exception:
            continue

      proj["skills_used"] = normalized

  return merged


async def parse_resume_text(resume_text: str) -> ParsedResume:
    """
    Full two-pass OpenRouter extraction pipeline.
    
    Pass 1: Full extraction of all resume fields.
    Pass 2: Gap check to find missed data and fix errors.
    Merge: Combine both passes taking best value per field.
    Validate: Ensure first_name and email are present.
    
    Parameters:
        resume_text: raw text extracted from resume file
        
    Returns:
        ParsedResume Pydantic model
        
    Raises:
        ValueError: if resume too short or critical fields missing
        Exception: if OpenRouter API calls fail
    """
    
    if len(resume_text.strip()) < 100:
        raise ValueError(
            "Resume text too short (min 100 characters). "
            "File may be empty or unreadable."
        )
    
    total_start = time.time()
    
    # ── PASS 1 ──────────────────────────────────────
    print("=" * 55)
    print("[OPENROUTER PASS 1] Starting full extraction...")
    print(f"[OPENROUTER PASS 1] Resume length: {len(resume_text)} chars")
    pass1_start = time.time()
    
    user_message_pass1 = f"""Extract all data from the resume below.
Return ONLY a JSON object that exactly matches this schema.
Every field must be present. Missing values must be null.

===== RESUME TEXT START =====
{resume_text}
===== RESUME TEXT END =====

===== REQUIRED JSON SCHEMA =====
{JSON_SCHEMA_TEMPLATE}"""

    pass1_result = await call_llm(SYSTEM_PROMPT_PASS1, user_message_pass1)
    pass1_elapsed = time.time() - pass1_start
    
    print(f"[OPENROUTER PASS 1] ✓ Complete in {pass1_elapsed:.2f}s")
    print(f"[OPENROUTER PASS 1] Name: {pass1_result.get('first_name')} {pass1_result.get('last_name')}")
    print(f"[OPENROUTER PASS 1] Email: {pass1_result.get('email')}")
    print(f"[OPENROUTER PASS 1] Skills: {len(pass1_result.get('skills') or [])}")
    print(f"[OPENROUTER PASS 1] Projects: {len(pass1_result.get('projects') or [])}")
    
    # ── PASS 2 ──────────────────────────────────────
    print(f"[OPENROUTER PASS 2] Starting gap check...")
    pass2_start = time.time()
    
    user_message_pass2 = f"""Here is the original resume text:
===== RESUME TEXT START =====
{resume_text}
===== RESUME TEXT END =====

Here is the JSON extracted in the first pass:
===== EXTRACTED JSON START =====
{json.dumps(pass1_result, indent=2)}
===== EXTRACTED JSON END =====

Re-read the resume carefully line by line.
Find anything that was missed or incorrect.
Return the corrected complete JSON."""

    try:
        pass2_result = await call_llm(SYSTEM_PROMPT_PASS2, user_message_pass2)
        pass2_elapsed = time.time() - pass2_start
        print(f"[OPENROUTER PASS 2] ✓ Complete in {pass2_elapsed:.2f}s")
    except Exception as e:
        pass2_elapsed = time.time() - pass2_start
        print(f"[OPENROUTER PASS 2] ⚠ Failed ({pass2_elapsed:.2f}s): {e}")
        print(f"[OPENROUTER PASS 2] Using Pass 1 result only")
        logger.warning(f"Pass 2 failed, using Pass 1: {e}")
        pass2_result = pass1_result
    
    # ── MERGE ───────────────────────────────────────
    print(f"[OPENROUTER MERGE] Merging pass results...")
    merged = merge_pass1_and_pass2(pass1_result, pass2_result)
    
    # Normalize fields that may come in wrong types from LLM
    print(f"[OPENROUTER] Before normalize - education items: {len(merged.get('education', []))}")
    if merged.get('education') and len(merged['education']) > 0:
        print(f"[OPENROUTER] First education start_year type: {type(merged['education'][0].get('start_year'))}, value: {merged['education'][0].get('start_year')}")
    
    merged = normalize_merged(merged)
    
    print(f"[OPENROUTER] After normalize - education items: {len(merged.get('education', []))}")
    if merged.get('education') and len(merged['education']) > 0:
        print(f"[OPENROUTER] First education start_year type: {type(merged['education'][0].get('start_year'))}, value: {merged['education'][0].get('start_year')}")
        print(f"[OPENROUTER] First education end_year type: {type(merged['education'][0].get('end_year'))}, value: {merged['education'][0].get('end_year')}")
    
    # ── VALIDATE ────────────────────────────────────
    if not merged.get("first_name") and not merged.get("email"):
        raise ValueError(
            "OpenRouter failed to extract first_name or email. "
            "Resume may be unreadable or in unsupported format."
        )
    
    total_elapsed = time.time() - total_start
    
    print("=" * 55)
    print(f"[OPENROUTER TIMING SUMMARY]")
    print(f"  Pass 1 (extraction) : {pass1_elapsed:.2f}s")
    print(f"  Pass 2 (gap check)  : {pass2_elapsed:.2f}s")
    print(f"  TOTAL               : {total_elapsed:.2f}s")
    print(f"[OPENROUTER] Student: {merged.get('first_name')} {merged.get('last_name')}")
    print(f"[OPENROUTER] Email  : {merged.get('email')}")
    print("=" * 55)
    
    logger.info(f"[OPENROUTER] Complete in {total_elapsed:.2f}s")
    
    # Final safety check: manually ensure education years are integers
    if merged.get('education'):
        for i, edu in enumerate(merged['education']):
            for year_field in ['start_year', 'end_year']:
                val = edu.get(year_field)
                if val is not None and not isinstance(val, int):
                    print(f"[CRITICAL] Education[{i}].{year_field} is still {type(val)}: {val}")
                    import re
                    if isinstance(val, str):
                        m = re.search(r'(\d{4})', val)
                        if m:
                            edu[year_field] = int(m.group(1))
                            print(f"[FIXED] Converted to {edu[year_field]}")
    
    try:
        return ParsedResume(**merged)
    except Exception as e:
        logger.error(f"Failed to create ParsedResume: {e}")
        logger.error(f"Education data: {merged.get('education', [])[:1]}")  # Log first education item for debugging
        raise


async def test_openrouter_connection() -> bool:
    """
    Quick test to verify OpenRouter API key and connection work.
    Call this from /health endpoint to verify setup.
    Returns True if working, False if not.
    """
    try:
        print("[OPENROUTER TEST] Testing connection...")
        result = await asyncio.wait_for(
            _call_openrouter_api("Reply with: ok"),
            timeout=30.0
        )
        print(f"[OPENROUTER TEST] ✓ Connection works: {result[:50]}")
        return True
    except Exception as e:
        print(f"[OPENROUTER TEST] ✗ Connection failed: {e}")
        return False
