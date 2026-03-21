# Resume Parser API

A FastAPI-based Resume Parsing System that automatically extracts resume data and fills the `campus5` MySQL database.

## Features

- **PDF & DOCX Extraction**: Extract text from PDF resumes and Word documents (.docx)
- **LLM-Powered Parsing**: Two-pass local Ollama LLM pipeline for accurate data extraction and gap-checking
- **Automatic DB Population**: Fills the campus5 database with student, education, skills, certifications, and more
- **RESTful API**: Clean, organized endpoints grouped by functionality
- **Master Data Management**: Automatic find-or-create for master tables (skills, languages, interests, etc.)
- **Duplicate Detection**: SHA-256 hashing to prevent duplicate resume processing
- **Comprehensive Logging**: INFO-level logging for all major operations

## Project Structure

```
resume_parser/
├── main.py                    # FastAPI app creation and router registration
├── config.py                  # Settings management
├── database.py                # SQLAlchemy async setup
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
│
├── models/                    # SQLAlchemy ORM models
│   ├── student_model.py
│   ├── education_model.py
│   ├── workexp_model.py
│   ├── project_model.py
│   ├── master_model.py
│   ├── address_model.py
│   └── m2m_model.py
│
├── schemas/                   # Pydantic v2 request/response schemas
│   ├── common_schema.py
│   ├── extract_schema.py
│   ├── parse_schema.py
│   ├── lookup_schema.py
│   ├── student_schema.py
│   ├── education_schema.py
│   ├── workexp_schema.py
│   ├── project_schema.py
│   └── address_schema.py
│
├── routers/                   # FastAPI routers (API endpoints)
│   ├── extract_router.py      # /extract/* endpoints
│   ├── parse_router.py        # /parse/* endpoints
│   ├── lookup_router.py       # /lookup/* endpoints
│   ├── save_router.py         # /save/* endpoints
│   └── orchestrator_router.py # /resume/* endpoints
│
├── services/                  # Business logic
│   ├── extract_service.py
│   ├── llm_service.py
│   ├── lookup_service.py
│   ├── save_service.py
│   └── orchestrator_service.py
│
└── utils/                     # Utility functions
    ├── response_utils.py
    ├── hash_utils.py
    └── date_utils.py
```

## Installation

### 1. Prerequisites

- Python 3.8+
- MySQL 5.7+
- Ollama (for local LLM) - https://ollama.ai

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit .env with your values
# - OLLAMA_MODEL: Local model name (default: llama3.1)
# - OLLAMA_BASE_URL: Ollama server URL (default: http://localhost:11434)
# - DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME: MySQL credentials
```

### 5. Verify Database

Ensure the `campus5` database exists and all required tables are created. The API assumes:
- Tables already exist (no migrations performed)
- All master data is pre-seeded (countries, states, cities, etc.)

## Running the API

### Development (with auto-reload)

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Supported File Formats

The API supports exactly **two** resume file formats:
- **PDF (.pdf)** - Extract text using PyMuPDF (fitz)
- **Word Documents (.docx)** - Extract text using python-docx

## API Endpoints

### Extract (Text Extraction)
- `POST /extract/pdf-to-text` — Extract text from PDF
- `POST /extract/docx-to-text` — Extract text from DOCX Word document

### Parse (LLM Parsing)
- `POST /parse/resume` — Parse resume text with LLM (2 passes)

### Lookup (Master Table Find-or-Create)
- `POST /lookup/skill` — Find or create skill
- `POST /lookup/language` — Find or create language
- `POST /lookup/interest` — Find or create interest
- `POST /lookup/certification` — Find or create certification
- `POST /lookup/college` — Find or create college
- `POST /lookup/course` — Find or create course
- `POST /lookup/salutation` — Find salutation (read-only)
- `POST /lookup/pincode` — Find pincode (read-only)

### Save (Database Insert)
- `POST /save/student` — Save student record
- `POST /save/school` — Save school record
- `POST /save/education` — Save college education
- `POST /save/workexp` — Save work experience
- `POST /save/project` — Save project
- `POST /save/project-skill` — Link project to skill
- `POST /save/student-skill` — Link student to skill
- `POST /save/student-language` — Link student to language
- `POST /save/student-interest` — Link student to interest
- `POST /save/student-certification` — Link student to certification
- `POST /save/address` — Save address

### Resume (Full Pipeline)
- `POST /resume/upload` — Upload resume file (PDF or DOCX) and run complete pipeline

## Example Usage

### Quick Test: Full Pipeline

```bash
# Upload a PDF resume
curl -X POST "http://localhost:8000/resume/upload" \
  -F "file=@resume.pdf"

# Or upload a DOCX resume
curl -X POST "http://localhost:8000/resume/upload" \
  -F "file=@resume.docx"
```

Response:
```json
{
  "success": true,
  "data": {
    "student_id": 101,
    "resume_hash": "abc123def456...",
    "already_existed": false,
    "summary": {
      "schools_saved": 1,
      "educations_saved": 1,
      "workexps_saved": 2,
      "projects_saved": 3,
      "skills_saved": 10,
      "languages_saved": 2,
      "certifications_saved": 1,
      "interests_saved": 2,
      "addresses_saved": 1
    },
    "warnings": []
  }
}
```

## Database Requirements

### Tables (Must Exist)

The API assumes these tables already exist in the `campus5` database:

**Master Tables (Read-Only):**
- `tbl_cp_msalutation`
- `tbl_cp_mlanguages`
- `tbl_cp_minterests`
- `tbl_cp_mcourses`
- `tbl_cp_mcolleges`
- `tbl_cp_mcertifications`
- `tbl_cp_mskills`
- `tbl_cp_mcountries`
- `tbl_cp_mstates`
- `tbl_cp_mcities`
- `tbl_cp_mpincodes`

**Student Tables:**
- `tbl_cp_student`
- `tbl_cp_student_school`
- `tbl_cp_student_education`
- `tbl_cp_student_workexp`
- `tbl_cp_studentprojects`
- `tbl_cp_student_address`

**Many-to-Many Tables:**
- `tbl_cp_m2m_std_skill`
- `tbl_cp_m2m_std_lng`
- `tbl_cp_m2m_std_interest`
- `tbl_cp_m2m_student_certification`
- `tbl_cp_m2m_studentproject_skill`

**Auto-Created:**
- `tbl_cp_resume_hashes` (created on startup if not exists)

## Architecture

### Two-Pass LLM Pipeline

1. **Pass 1 - Extraction**: Initial resume parsing to extract all data into structured JSON
2. **Pass 2 - Gap Checking**: Review extracted data and fix missing information, correct errors

This dual-pass approach ensures:
- High data quality
- Minimal missed information
- Automatic error correction
- Inference of implicit data (e.g., "intern" designation → internship type)

### Service Layers

- **Extract Service**: PDF/image text extraction
- **LLM Service**: Claude API calls with dual-pass logic
- **Lookup Service**: Master table management (find-or-create)
- **Save Service**: Database insert operations
- **Orchestrator Service**: 15-step full pipeline coordination

## Error Handling

All endpoints return standardized JSON responses:

**Success:**
```json
{
  "success": true,
  "data": { ... }
}
```

**Error:**
```json
{
  "success": false,
  "error": "Human readable error message",
  "detail": "Technical details or null"
}
```

## Configuration

All settings loaded from `.env`:

```env
# Anthropic
ANTHROPIC_API_KEY=your_key_here
CLAUDE_MODEL=claude-sonnet-4-20250514
CLAUDE_MAX_TOKENS=4096
CLAUDE_TEMPERATURE=0

# MySQL
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=password
DB_NAME=campus5

# App
APP_ENV=development
APP_PORT=8000
MAX_FILE_SIZE_MB=10
ALLOWED_EXTENSIONS=pdf,png,jpg,jpeg
```

## Logging

All major operations are logged at INFO level:

```
2024-03-21 10:15:30 INFO STEP 1 — Extract text
2024-03-21 10:15:31 INFO Step 1 complete: extracted 5234 chars
2024-03-21 10:15:32 INFO STEP 2 — Duplicate check
2024-03-21 10:15:32 INFO Step 2 complete: no duplicate found
2024-03-21 10:15:35 INFO STEP 3 — LLM Parse (2 passes)
2024-03-21 10:15:40 INFO Step 3 complete: LLM parsing done
...
```

## Performance Notes

- **First resume**: ~15-20 seconds (2 LLM calls)
- **Concurrent requests**: Limited by Claude API rate limits
- **Database**: Async operations for non-blocking I/O
- **Memory**: ~500MB typical usage

## Troubleshooting

### "Import could not be resolved" in IDE
This is normal until dependencies are installed. The code is correct.

### Tesseract not found
Set `PYTESSERACT_PATH` environment variable to tesseract executable location.

### MySQL connection refused
Verify credentials in `.env` and that MySQL server is running.

### Claude API errors
- Check `ANTHROPIC_API_KEY` is valid
- Verify account has API access enabled
- Check rate limits haven't been exceeded

### PDF extraction returns no text
PDFs may be scanned images. Use `/extract/image-to-text` instead or convert to images first.

## License

Internal project - Artiset Internship 2026
