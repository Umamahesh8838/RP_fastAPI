import ollama
import json
import re
import logging
from config import get_settings
from schemas.parse_schema import ParsedResume
from utils.hash_utils import compute_resume_hash

logger = logging.getLogger(__name__)

settings = get_settings()
client = ollama.Client(host=settings.ollama_base_url)

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
    Cleans JSON response by removing markdown code fences and parses it.
    Handles cases where Ollama returns broken or partial JSON.
    
    Parameters:
        raw_text (str): Raw LLM response text
        
    Returns:
        dict: Parsed JSON object
        
    Raises:
        ValueError: If JSON parsing fails after all attempts
    """
    clean = raw_text.strip()
    clean = re.sub(r'^```json\s*', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'^```\s*', '', clean)
    clean = re.sub(r'\s*```$', '', clean)
    clean = clean.strip()
    
    # Attempt 1: Try normal json.loads() first
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass
    
    # Attempt 2: If that fails, try to extract JSON from text
    # Find first { and last } to handle cases where Ollama adds text before/after JSON
    first_brace = clean.find('{')
    last_brace = clean.rfind('}')
    
    if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
        json_substring = clean[first_brace:last_brace + 1]
        try:
            return json.loads(json_substring)
        except json.JSONDecodeError:
            pass
    
    # Attempt 3: If all else fails, log and raise
    logger.debug(f"LLM returned invalid JSON. Raw response:\n{raw_text}")
    raise ValueError(
        "LLM returned invalid JSON. Try a different model or check Ollama."
    )


async def call_llm(system_prompt: str, user_message: str) -> dict:
    """
    Makes one call to the Anthropic Claude API.
    
    Parameters:
        system_prompt (str): System prompt to guide the LLM
        user_message (str): User message/resume text
        
    Returns:
        dict: Parsed JSON response from LLM
        
    Raises:
        ValueError: If API call fails or response is not valid JSON
    """
    logger.debug(f"Calling Ollama LLM (model={settings.ollama_model})")

    try:
        # Combine system and user messages for Ollama
        full_message = f"{system_prompt}\n\n{user_message}"
        
        response = client.generate(
            model=settings.ollama_model,
            prompt=full_message,
            stream=False,
            options={
                "temperature": settings.claude_temperature,
                "top_p": 0.9,
            }
        )
        
        raw_text = response["response"]
        logger.debug("Received Ollama response, parsing JSON")
        
        return clean_and_parse_json(raw_text)
        
    except Exception as e:
        logger.error(f"Ollama API error: {str(e)}")
        raise ValueError(f"LLM API error: {str(e)}")


async def merge_pass1_and_pass2(pass1: dict, pass2: dict) -> dict:
    """
    Merges two LLM extraction passes.
    Pass 2 is treated as more authoritative (gap checking and corrections).
    
    Parameters:
        pass1 (dict): First pass extraction
        pass2 (dict): Second pass extraction (gap checking)
        
    Returns:
        dict: Merged result
    """
    logger.debug("Merging pass1 and pass2 results")
    
    # For most fields, prefer pass2 if not null
    merged = pass2.copy()
    
    return merged


def normalize_merged(merged: dict) -> dict:
  """
  Normalizes certain LLM output fields to match Pydantic schema types.

  - Convert education[].cgpa from strings like '3.8/4.0' or '3.8' to float 3.8
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

  # Normalize CGPA in education entries
  for edu in merged.get("education", []):
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
    Full two-pass LLM extraction pipeline.
    Pass 1: extract everything.
    Pass 2: find missed data and fix errors.
    Validates required fields after merge.
    
    Parameters:
        resume_text (str): Raw resume text
        
    Returns:
        ParsedResume: Validated Pydantic model
        
    Raises:
        ValueError: If required fields missing or parsing fails
    """
    logger.info("Starting two-pass LLM parsing")
    
    if len(resume_text.strip()) < 100:
        raise ValueError("Resume text must be at least 100 characters")
    
    # PASS 1: Initial extraction
    logger.info("Pass 1: Initial extraction")
    pass1_user_msg = f"Extract all data from this resume and return as JSON matching the schema:\n\n{JSON_SCHEMA_TEMPLATE}\n\nResume text:\n\n{resume_text}"
    
    pass1_result = await call_llm(SYSTEM_PROMPT_PASS1, pass1_user_msg)
    logger.debug(f"Pass 1 result: first_name={pass1_result.get('first_name')}, email={pass1_result.get('email')}")
    
    # PASS 2: Gap checking and corrections
    logger.info("Pass 2: Gap checking and corrections")
    pass2_user_msg = f"Original resume:\n\n{resume_text}\n\nAlready extracted JSON:\n\n{json.dumps(pass1_result, indent=2)}\n\nFix any gaps and errors in the JSON, return complete corrected JSON."
    
    pass2_result = await call_llm(SYSTEM_PROMPT_PASS2, pass2_user_msg)
    logger.debug(f"Pass 2 result: first_name={pass2_result.get('first_name')}, email={pass2_result.get('email')}")
    
    # Merge results (pass2 is more authoritative)
    merged = await merge_pass1_and_pass2(pass1_result, pass2_result)
    # Normalize fields that may come in wrong types from LLM
    merged = normalize_merged(merged)
    
    # Validate required fields
    if not merged.get('first_name'):
        raise ValueError("first_name is required but not found in resume")
    if not merged.get('email'):
        raise ValueError("email is required but not found in resume")
    
    logger.info("LLM parsing complete and validated")
    
    # Return as Pydantic model
    return ParsedResume(**merged)
