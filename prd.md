# GitHub Copilot Prompt — FastAPI Resume Parser System
# Paste this ENTIRE file into GitHub Copilot Chat
# Do NOT use inline suggestions — use the Copilot Chat panel

---

## PROJECT OVERVIEW

Build a complete **FastAPI-based Resume Parsing System** in Python.

The system:
1. Accepts a resume file (PDF or image) uploaded by a user
2. Extracts raw text from the file
3. Sends that text to the **Anthropic Claude LLM API exactly twice** (pass 1 + pass 2) to get structured JSON
4. Uses that structured JSON to fill the `campus5` MySQL database by calling small focused internal service functions

This is a **backend-only REST API project**. No frontend. No HTML. Everything is JSON in, JSON out.

The goal of this project is **automatic DB filling from a resume**. Every piece of data that can be extracted from a resume must be saved into the correct table and column in `campus5`.

---

## EXTREMELY IMPORTANT RULES — READ BEFORE WRITING A SINGLE LINE OF CODE

1. Use **FastAPI** — not Flask, not Django. Only FastAPI.
2. Use **MySQL** as the database. Use **PyMySQL** as the driver. Use **SQLAlchemy 2.x** as the ORM with `AsyncSession` for async DB operations.
3. Use the **Anthropic Python SDK** (`anthropic` package) to call Claude. Do not use `requests` or `httpx` directly.
4. The LLM must be called **exactly 2 times per resume** — pass 1 (full extraction) and pass 2 (gap check). Never more.
5. All endpoints return **JSON only**. No HTML, no redirects, no plain text.
6. Use **FastAPI Routers** (`APIRouter`) to separate route groups — one router per group in its own file.
7. Use **Pydantic v2** for ALL request bodies, response bodies, and data validation.
8. **ALL database column names, JSON field names, Pydantic field names, and Python variable names must EXACTLY match the MySQL column names** from the Database Schema section below. Same spelling, same underscore positions, same case. Do not rename, shorten, or alias anything.
9. Every function and class must have a **docstring** explaining: what it does, parameters, return value.
10. All errors must return this exact JSON shape:
    ```json
    { "success": false, "error": "human readable message", "detail": "technical detail or null" }
    ```
11. All success responses must return this exact JSON shape:
    ```json
    { "success": true, "data": { ... } }
    ```
12. Use **python-dotenv** to load all config from a `.env` file. Zero hardcoded secrets anywhere.
13. Use **PyMuPDF** (`fitz` package) for PDF-to-text extraction.
14. Use **Pillow** + **pytesseract** for image-to-text (OCR).
15. Use Python's built-in `logging` module at INFO level for all major steps.
16. Use **async/await** throughout — all route handlers, service functions, and DB calls must be async.
17. The API is split into the **smallest possible units** so each endpoint can be reused independently by any other system in the future. A skill lookup API should work for any system, not just resumes. A student save API should work for any student registration flow.

---

## PROJECT FOLDER STRUCTURE

Create exactly this structure. Do not add or remove files:

```
resume_parser/
│
├── main.py                            # FastAPI app creation, router registration, startup events
├── config.py                          # All settings loaded from .env using pydantic-settings
├── database.py                        # SQLAlchemy async engine, AsyncSession factory, get_db dependency
├── requirements.txt                   # All pip packages
├── .env.example                       # Template of all required env variables
├── .gitignore                         # Standard Python gitignore
│
├── models/                            # SQLAlchemy ORM models — one file per logical group
│   ├── __init__.py
│   ├── student_model.py               # tbl_cp_student
│   ├── education_model.py             # tbl_cp_student_school, tbl_cp_student_education
│   ├── workexp_model.py               # tbl_cp_student_workexp
│   ├── project_model.py               # tbl_cp_studentprojects
│   ├── master_model.py                # tbl_cp_msalutation, tbl_cp_mlanguages, tbl_cp_minterests,
│   │                                  # tbl_cp_mcourses, tbl_cp_mcolleges, tbl_cp_mcertifications,
│   │                                  # tbl_cp_mskills, tbl_cp_mcountries, tbl_cp_mstates,
│   │                                  # tbl_cp_mcities, tbl_cp_mpincodes, tbl_cp_minterviewer,
│   │                                  # tbl_cp_mmodule, tbl_cp_mdifficulty, tbl_cp_mround_result,
│   │                                  # tbl_cp_mattendance
│   ├── address_model.py               # tbl_cp_student_address
│   └── m2m_model.py                   # All many-to-many join tables
│
├── schemas/                           # Pydantic v2 schemas — one file per logical group
│   ├── __init__.py
│   ├── common_schema.py               # SuccessResponse, ErrorResponse, shared base models
│   ├── extract_schema.py              # Request/response for /extract/* endpoints
│   ├── parse_schema.py                # Full parsed resume structure (LLM output shape)
│   ├── student_schema.py              # Request/response for /save/student
│   ├── education_schema.py            # Request/response for /save/school and /save/education
│   ├── workexp_schema.py              # Request/response for /save/workexp
│   ├── project_schema.py              # Request/response for /save/project
│   ├── address_schema.py              # Request/response for /save/address
│   └── lookup_schema.py               # Request/response for all /lookup/* endpoints
│
├── routers/                           # FastAPI APIRouter — one file per API group
│   ├── __init__.py
│   ├── extract_router.py              # /extract/* — PDF and image to text
│   ├── parse_router.py                # /parse/* — LLM call
│   ├── lookup_router.py               # /lookup/* — master table find-or-create
│   ├── save_router.py                 # /save/* — DB insert for each entity
│   └── orchestrator_router.py         # /resume/* — full pipeline
│
├── services/                          # Business logic — no FastAPI imports here, pure Python async
│   ├── __init__.py
│   ├── extract_service.py             # PDF and image text extraction
│   ├── llm_service.py                 # Anthropic API calls, pass1+pass2, merge logic
│   ├── lookup_service.py              # All master table find-or-create functions
│   ├── save_service.py                # All DB insert functions
│   └── orchestrator_service.py        # Full pipeline logic calling all services in order
│
└── utils/
    ├── __init__.py
    ├── response_utils.py              # success_response() and error_response() helpers
    ├── hash_utils.py                  # SHA-256 hash of resume text for duplicate detection
    └── date_utils.py                  # Date string to Python date conversion helpers
```

---

## ENVIRONMENT VARIABLES (.env.example)

```env
# Anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key_here
CLAUDE_MODEL=claude-sonnet-4-20250514
CLAUDE_MAX_TOKENS=4096
CLAUDE_TEMPERATURE=0

# MySQL Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=campus5

# App
APP_ENV=development
APP_PORT=8000
MAX_FILE_SIZE_MB=10
ALLOWED_EXTENSIONS=pdf,png,jpg,jpeg
```

---

## config.py — FULL IMPLEMENTATION

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """All application settings loaded from .env file."""

    # Anthropic
    anthropic_api_key: str
    claude_model: str = "claude-sonnet-4-20250514"
    claude_max_tokens: int = 4096
    claude_temperature: float = 0.0

    # MySQL
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "campus5"

    # App
    app_env: str = "development"
    app_port: int = 8000
    max_file_size_mb: int = 10
    allowed_extensions: str = "pdf,png,jpg,jpeg"

    @property
    def database_url(self) -> str:
        """Builds async SQLAlchemy connection string for MySQL."""
        return f"mysql+aiomysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [ext.strip().lower() for ext in self.allowed_extensions.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    """Returns cached settings instance."""
    return Settings()
```

---

## database.py — FULL IMPLEMENTATION

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass

async def get_db() -> AsyncSession:
    """
    FastAPI dependency that yields an async DB session.
    Automatically closes session after request completes.
    Usage: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

---

## DATABASE SCHEMA — campus5

The MySQL database is named `campus5`. All tables below already exist — do NOT create them or run migrations. Just define ORM models that map to them.

Use these EXACT table names and column names everywhere: in ORM models, in Pydantic schemas, in service functions, in SQL queries, in JSON responses. No exceptions.

### tbl_cp_msalutation
| Column | Type | Notes |
|---|---|---|
| row_id | INT AUTO_INCREMENT PK | |
| salutation_id | INT NOT NULL UNIQUE | Used as the business key |
| value | VARCHAR(50) NOT NULL UNIQUE | e.g. "Mr.", "Ms.", "Dr.", "Prof.", "Mrs." |
| description | VARCHAR(255) DEFAULT 'No description' | |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### tbl_cp_mlanguages
| Column | Type | Notes |
|---|---|---|
| row_id | INT AUTO_INCREMENT PK | |
| language_id | INT NOT NULL UNIQUE | Business key |
| language_code | VARCHAR(20) NOT NULL UNIQUE | e.g. "ENG", "HIN", "TAM" |
| language_name | VARCHAR(100) NOT NULL UNIQUE | e.g. "English", "Hindi", "Tamil" |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### tbl_cp_minterests
| Column | Type | Notes |
|---|---|---|
| row_id | INT AUTO_INCREMENT PK | |
| interest_id | INT NOT NULL UNIQUE | Business key |
| name | VARCHAR(150) NOT NULL UNIQUE | e.g. "Machine Learning", "Web Development", "Data Science" |
| created_at | DATETIME | |
| updated_at | DATETIME | |

**NOTE on interests**: This table stores the DOMAIN/AREA a student is interested in (like "Web Development", "Cybersecurity", "Data Science") — NOT hobbies like "reading" or "cricket". Extract these from resume sections titled "Areas of Interest", "Career Interests", or infer from the overall profile (if student has 4+ ML projects → infer "Machine Learning").

### tbl_cp_mcourses
| Column | Type | Notes |
|---|---|---|
| row_id | INT AUTO_INCREMENT PK | |
| course_id | INT NOT NULL UNIQUE | Business key |
| course_name | VARCHAR(150) NOT NULL | e.g. "Bachelor of Technology" |
| course_code | VARCHAR(50) NOT NULL | e.g. "BTECH" |
| specialization_name | VARCHAR(150) NOT NULL DEFAULT 'General' | e.g. "Computer Science", "Finance" |
| specialization_code | VARCHAR(50) NOT NULL DEFAULT 'GEN' | e.g. "CS", "FIN" |
| created_at | DATETIME | |
| updated_at | DATETIME | |
| UNIQUE | (course_code, specialization_code) | |
| UNIQUE | (course_name, specialization_name) | |

### tbl_cp_mcolleges
| Column | Type | Notes |
|---|---|---|
| row_id | INT AUTO_INCREMENT PK | |
| college_id | INT NOT NULL UNIQUE | Business key |
| college_name | VARCHAR(255) NOT NULL UNIQUE | Full name of the college |
| spoc_name | VARCHAR(150) DEFAULT 'Not Assigned' | |
| spoc_phone | VARCHAR(20) DEFAULT '0000000000' | |
| spoc_email | VARCHAR(255) DEFAULT 'noreply@college.com' | |
| tpo_name | VARCHAR(150) DEFAULT 'Not Assigned' | |
| tpo_phone | VARCHAR(20) DEFAULT '0000000000' | |
| tpo_email | VARCHAR(255) DEFAULT 'noreply@college.com' | |
| student_coordinator_name | VARCHAR(150) DEFAULT 'Not Assigned' | |
| student_coordinator_phone | VARCHAR(20) DEFAULT '0000000000' | |
| student_coordinator_email | VARCHAR(255) DEFAULT 'noreply@college.com' | |
| reference_details | TEXT nullable | |
| priority | INT NOT NULL DEFAULT 5 | 1-10 scale |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### tbl_cp_mcertifications
| Column | Type | Notes |
|---|---|---|
| row_id | INT AUTO_INCREMENT PK | |
| certification_id | INT NOT NULL UNIQUE | Business key |
| certification_name | VARCHAR(255) NOT NULL | Full cert name |
| certification_code | VARCHAR(100) NOT NULL UNIQUE | e.g. "AWS-CCP", "GCP-ACE" |
| issuing_organization | VARCHAR(255) NOT NULL | e.g. "Amazon Web Services", "Google" |
| certification_type | VARCHAR(100) DEFAULT 'General' | e.g. "Cloud", "Data Science", "Cybersecurity" |
| mode | VARCHAR(50) DEFAULT 'Online' | |
| validity_period_value | INT DEFAULT 0 | |
| validity_period_unit | VARCHAR(20) DEFAULT 'Years' | |
| is_lifetime | BOOLEAN nullable | true if no expiry |
| created_at | DATETIME | |
| updated_at | DATETIME | |
| UNIQUE | (certification_name, issuing_organization) | |

### tbl_cp_mskills
| Column | Type | Notes |
|---|---|---|
| row_id | INT AUTO_INCREMENT PK | |
| skill_id | INT NOT NULL UNIQUE | Business key |
| name | VARCHAR(100) NOT NULL UNIQUE | e.g. "Python", "React.js", "Docker" |
| description | VARCHAR(255) DEFAULT 'No description' | |
| language_id | INT NOT NULL FK → tbl_cp_mlanguages(language_id) | The programming/spoken language category |
| version | VARCHAR(50) DEFAULT 'N/A' | |
| complexity | VARCHAR(50) DEFAULT 'Beginner' | values: "Beginner", "Intermediate", "Expert" |
| status | VARCHAR(30) DEFAULT 'Active' | |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### tbl_cp_mcountries
| Column | Type | Notes |
|---|---|---|
| row_id | INT AUTO_INCREMENT PK | |
| country_id | INT NOT NULL UNIQUE | Business key |
| country_name | VARCHAR(100) NOT NULL UNIQUE | |
| country_code | VARCHAR(5) NOT NULL UNIQUE | e.g. "IN", "US" |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### tbl_cp_mstates
| Column | Type | Notes |
|---|---|---|
| row_id | INT AUTO_INCREMENT PK | |
| state_id | INT NOT NULL UNIQUE | Business key |
| state_name | VARCHAR(100) NOT NULL | |
| state_code | VARCHAR(10) DEFAULT 'XX' | |
| country_id | INT NOT NULL FK → tbl_cp_mcountries(country_id) | |
| created_at | DATETIME | |
| updated_at | DATETIME | |
| UNIQUE | (state_name, country_id) | |

### tbl_cp_mcities
| Column | Type | Notes |
|---|---|---|
| row_id | INT AUTO_INCREMENT PK | |
| city_id | INT NOT NULL UNIQUE | Business key |
| city_name | VARCHAR(100) NOT NULL | |
| state_id | INT NOT NULL FK → tbl_cp_mstates(state_id) | |
| created_at | DATETIME | |
| updated_at | DATETIME | |
| UNIQUE | (city_name, state_id) | |

### tbl_cp_mpincodes
| Column | Type | Notes |
|---|---|---|
| row_id | INT AUTO_INCREMENT PK | |
| pincode_id | INT NOT NULL UNIQUE | Business key |
| pincode | VARCHAR(20) NOT NULL UNIQUE | |
| city_id | INT NOT NULL FK → tbl_cp_mcities(city_id) | |
| area_name | VARCHAR(150) DEFAULT 'Unknown Area' | |
| created_at | DATETIME | |
| updated_at | DATETIME | |

**IMPORTANT**: tbl_cp_mpincodes, tbl_cp_mcities, tbl_cp_mstates, tbl_cp_mcountries are **READ-ONLY** master tables. The system only reads from them, never inserts into them. Geography data is pre-seeded by admins.

### tbl_cp_student
| Column | Type | Notes |
|---|---|---|
| row_id | INT AUTO_INCREMENT PK | |
| student_id | INT NOT NULL UNIQUE | Business key — use COALESCE(MAX(student_id),0)+1 |
| salutation_id | INT nullable FK → tbl_cp_msalutation(salutation_id) | |
| first_name | VARCHAR(100) NOT NULL | |
| middle_name | VARCHAR(100) DEFAULT '' | |
| last_name | VARCHAR(100) DEFAULT '' | |
| email | VARCHAR(255) NOT NULL UNIQUE | |
| alt_email | VARCHAR(255) DEFAULT '' | |
| contact_number | VARCHAR(20) UNIQUE nullable | |
| alt_contact_number | VARCHAR(20) DEFAULT '0000000000' | |
| linkedin_url | VARCHAR(255) DEFAULT '' | |
| github_url | VARCHAR(255) DEFAULT '' | |
| portfolio_url | VARCHAR(255) DEFAULT '' | |
| resume_url | VARCHAR(500) DEFAULT '' | |
| profile_photo_url | VARCHAR(500) NOT NULL DEFAULT 'default_profile.png' | |
| date_of_birth | DATE NOT NULL DEFAULT '1900-01-01' | Use '1900-01-01' when not provided |
| current_city | VARCHAR(100) DEFAULT 'Not Specified' | |
| gender | VARCHAR(20) DEFAULT 'Not Specified' | |
| user_type | VARCHAR(100) DEFAULT 'Student' | |
| is_active | BOOLEAN nullable | |
| status | VARCHAR(30) NOT NULL DEFAULT 'Active' | |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### tbl_cp_student_school
| Column | Type | Notes |
|---|---|---|
| row_id | INT AUTO_INCREMENT PK | |
| school_id | INT NOT NULL UNIQUE | Business key — use COALESCE(MAX(school_id),0)+1 |
| student_id | INT NOT NULL FK → tbl_cp_student(student_id) | |
| standard | VARCHAR(50) NOT NULL | e.g. "10th", "12th" |
| board | VARCHAR(100) DEFAULT 'Not Specified' | e.g. "CBSE", "ICSE", "Maharashtra State Board" |
| school_name | VARCHAR(255) DEFAULT 'Not Specified' | |
| percentage | DECIMAL(5,2) NOT NULL DEFAULT 0.00 | |
| passing_year | INT DEFAULT 0 | |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### tbl_cp_student_education
| Column | Type | Notes |
|---|---|---|
| row_id | INT AUTO_INCREMENT PK | |
| edu_id | INT NOT NULL UNIQUE | Business key — use COALESCE(MAX(edu_id),0)+1 |
| student_id | INT NOT NULL FK → tbl_cp_student(student_id) | |
| college_id | INT NOT NULL FK → tbl_cp_mcolleges(college_id) | |
| course_id | INT NOT NULL FK → tbl_cp_mcourses(course_id) | |
| start_year | INT DEFAULT 0 | |
| end_year | INT DEFAULT 0 | null if currently studying |
| cgpa | DECIMAL(4,2) DEFAULT 0.00 | |
| percentage | DECIMAL(5,2) DEFAULT 0.00 | fill only if explicitly stated |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### tbl_cp_student_workexp
| Column | Type | Notes |
|---|---|---|
| row_id | INT AUTO_INCREMENT PK | |
| workexp_id | INT NOT NULL UNIQUE | Business key — use COALESCE(MAX(workexp_id),0)+1 |
| student_id | INT NOT NULL FK → tbl_cp_student(student_id) | |
| company_name | VARCHAR(255) NOT NULL | |
| company_location | VARCHAR(150) DEFAULT 'Not Specified' | city or city+country |
| designation | VARCHAR(150) DEFAULT 'Not Specified' | exact job title as written |
| employment_type | VARCHAR(50) DEFAULT 'Full-Time' | values: "Full-Time", "Part-Time", "Internship", "Freelance", "Contract" |
| start_date | DATE NOT NULL DEFAULT '1900-01-01' | |
| end_date | DATE DEFAULT '1900-01-01' | Use '1900-01-01' when is_current = true |
| is_current | BOOLEAN nullable | true if currently working here |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### tbl_cp_studentprojects
| Column | Type | Notes |
|---|---|---|
| row_id | INT AUTO_INCREMENT PK | |
| project_id | INT NOT NULL UNIQUE | Business key — use COALESCE(MAX(project_id),0)+1 |
| student_id | INT NOT NULL FK → tbl_cp_student(student_id) | |
| workexp_id | INT nullable FK → tbl_cp_student_workexp(workexp_id) | link if project was done at a company |
| project_title | VARCHAR(255) NOT NULL | |
| project_description | TEXT nullable | full description as written |
| achievements | TEXT nullable | outcomes, results, impact if mentioned |
| project_start_date | DATE DEFAULT '1900-01-01' | |
| project_end_date | DATE DEFAULT '1900-01-01' | |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### tbl_cp_student_address
| Column | Type | Notes |
|---|---|---|
| row_id | INT AUTO_INCREMENT PK | |
| address_id | INT NOT NULL UNIQUE | Business key — use COALESCE(MAX(address_id),0)+1 |
| student_id | INT NOT NULL FK → tbl_cp_student(student_id) | |
| address_line_1 | VARCHAR(255) NOT NULL | house/flat/building |
| address_line_2 | VARCHAR(255) DEFAULT '' | area/locality |
| care_of | VARCHAR(255) DEFAULT '' | |
| landmark | VARCHAR(255) DEFAULT 'No Landmark' | |
| pincode_id | INT NOT NULL FK → tbl_cp_mpincodes(pincode_id) | must be resolved before saving |
| latitude | DECIMAL(10,8) DEFAULT 0.00000000 | |
| longitude | DECIMAL(11,8) DEFAULT 0.00000000 | |
| address_type | VARCHAR(50) NOT NULL DEFAULT 'current' | values: "current", "permanent" |
| address_expiry | DATE DEFAULT '9999-12-31' | |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### Many-to-Many Tables

#### tbl_cp_m2m_std_skill
| Column | Type | Notes |
|---|---|---|
| row_id | INT AUTO_INCREMENT PK | |
| student_id | INT NOT NULL FK → tbl_cp_student(student_id) | |
| skill_id | INT NOT NULL FK → tbl_cp_mskills(skill_id) | |
| created_at | DATETIME | |
| updated_at | DATETIME | |
| UNIQUE | (student_id, skill_id) | |

#### tbl_cp_m2m_std_lng
| Column | Type | Notes |
|---|---|---|
| row_id | INT AUTO_INCREMENT PK | |
| student_id | INT NOT NULL FK → tbl_cp_student(student_id) | |
| language_id | INT NOT NULL FK → tbl_cp_mlanguages(language_id) | |
| created_at | DATETIME | |
| updated_at | DATETIME | |
| UNIQUE | (student_id, language_id) | |

#### tbl_cp_m2m_std_interest
| Column | Type | Notes |
|---|---|---|
| row_id | INT AUTO_INCREMENT PK | |
| student_id | INT NOT NULL FK → tbl_cp_student(student_id) | |
| interest_id | INT NOT NULL FK → tbl_cp_minterests(interest_id) | |
| created_at | DATETIME | |
| updated_at | DATETIME | |
| UNIQUE | (student_id, interest_id) | |

#### tbl_cp_m2m_student_certification
| Column | Type | Notes |
|---|---|---|
| row_id | INT AUTO_INCREMENT PK | |
| student_id | INT NOT NULL FK → tbl_cp_student(student_id) | |
| certification_id | INT NOT NULL FK → tbl_cp_mcertifications(certification_id) | |
| issue_date | DATE DEFAULT '1900-01-01' | |
| expiry_date | DATE DEFAULT '9999-12-31' | '9999-12-31' means no expiry |
| certificate_url | VARCHAR(500) DEFAULT '' | |
| credential_id | VARCHAR(150) DEFAULT '' | |
| is_verified | BOOLEAN nullable | |
| created_at | DATETIME | |
| updated_at | DATETIME | |
| UNIQUE | (student_id, certification_id) | |

#### tbl_cp_m2m_studentproject_skill
| Column | Type | Notes |
|---|---|---|
| row_id | INT AUTO_INCREMENT PK | |
| project_id | INT NOT NULL FK → tbl_cp_studentprojects(project_id) | |
| skill_id | INT NOT NULL FK → tbl_cp_mskills(skill_id) | |
| created_at | DATETIME | |
| updated_at | DATETIME | |
| UNIQUE | (project_id, skill_id) | |

### Extra Table — tbl_cp_resume_hashes (CREATE THIS — does not exist yet)
| Column | Type | Notes |
|---|---|---|
| hash | VARCHAR(64) NOT NULL PRIMARY KEY | SHA-256 of resume text |
| student_id | INT NOT NULL | which student this resume belongs to |
| created_at | DATETIME DEFAULT CURRENT_TIMESTAMP | |

Create this table on startup using:
```sql
CREATE TABLE IF NOT EXISTS tbl_cp_resume_hashes (
    hash       VARCHAR(64)  NOT NULL PRIMARY KEY,
    student_id INT          NOT NULL,
    created_at DATETIME     DEFAULT CURRENT_TIMESTAMP
);
```

---

## PYDANTIC SCHEMAS — COMPLETE SPECIFICATION

### schemas/common_schema.py

```python
from pydantic import BaseModel
from typing import Any, Optional

class SuccessResponse(BaseModel):
    """Standard success response wrapper for all endpoints."""
    success: bool = True
    data: Any

class ErrorResponse(BaseModel):
    """Standard error response wrapper for all endpoints."""
    success: bool = False
    error: str
    detail: Optional[str] = None
```

### schemas/extract_schema.py

```python
from pydantic import BaseModel

class PDFExtractResponse(BaseModel):
    """Response after extracting text from a PDF file."""
    text: str               # full extracted text
    page_count: int         # number of pages in the PDF
    char_count: int         # total character count of extracted text

class ImageExtractResponse(BaseModel):
    """Response after extracting text from a resume image using OCR."""
    text: str               # full extracted text
    char_count: int         # total character count
```

### schemas/parse_schema.py

```python
from pydantic import BaseModel
from typing import Optional, List

class SchoolItem(BaseModel):
    """One school education entry extracted from resume."""
    standard: Optional[str] = None           # "10th" or "12th"
    board: Optional[str] = None              # "CBSE", "ICSE", "Maharashtra State Board"
    school_name: Optional[str] = None
    percentage: Optional[float] = None       # decimal e.g. 85.60
    passing_year: Optional[int] = None       # e.g. 2018

class EducationItem(BaseModel):
    """One college/university education entry extracted from resume."""
    college_name: Optional[str] = None       # full institution name
    course_name: Optional[str] = None        # "Bachelor of Technology"
    specialization_name: Optional[str] = None  # "Computer Science"
    start_year: Optional[int] = None
    end_year: Optional[int] = None           # null if currently studying
    cgpa: Optional[float] = None
    percentage: Optional[float] = None       # fill only if explicitly stated

class WorkExpItem(BaseModel):
    """One work experience entry extracted from resume."""
    company_name: Optional[str] = None
    company_location: Optional[str] = None   # city or city+country
    designation: Optional[str] = None        # exact job title as written
    employment_type: Optional[str] = None    # "Full-Time","Part-Time","Internship","Freelance","Contract"
    start_date: Optional[str] = None         # YYYY-MM-DD
    end_date: Optional[str] = None           # YYYY-MM-DD or null if is_current
    is_current: Optional[bool] = None

class ProjectItem(BaseModel):
    """One project entry extracted from resume."""
    project_title: Optional[str] = None
    project_description: Optional[str] = None
    achievements: Optional[str] = None       # outcomes/results/impact
    project_start_date: Optional[str] = None # YYYY-MM-DD
    project_end_date: Optional[str] = None   # YYYY-MM-DD
    workexp_company_name: Optional[str] = None  # company name if project was done at an employer
    skills_used: List[str] = []              # list of skill name strings used in this project

class SkillItem(BaseModel):
    """One skill entry extracted from resume."""
    name: Optional[str] = None
    complexity: Optional[str] = None         # "Beginner", "Intermediate", "Expert"

class LanguageItem(BaseModel):
    """One spoken/written language entry extracted from resume."""
    language_name: Optional[str] = None      # "English", "Hindi", "Tamil"

class CertificationItem(BaseModel):
    """One certification entry extracted from resume."""
    certification_name: Optional[str] = None
    issuing_organization: Optional[str] = None  # "Coursera", "Amazon Web Services"
    certification_type: Optional[str] = None    # "Cloud", "Data Science"
    issue_date: Optional[str] = None            # YYYY-MM-DD
    expiry_date: Optional[str] = None           # YYYY-MM-DD
    is_lifetime: Optional[bool] = None          # true if no expiry mentioned
    certificate_url: Optional[str] = None
    credential_id: Optional[str] = None

class InterestItem(BaseModel):
    """
    One domain/area interest extracted from resume.
    This is NOT hobbies. This is career domain interest like:
    "Machine Learning", "Web Development", "Cybersecurity", "Data Science", "Cloud Computing"
    """
    name: Optional[str] = None
    is_inferred: Optional[bool] = None   # true if inferred from profile, false if explicitly stated

class AddressItem(BaseModel):
    """One address entry extracted from resume."""
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    landmark: Optional[str] = None
    pincode: Optional[str] = None        # raw pincode string — will be looked up later
    city_name: Optional[str] = None
    state_name: Optional[str] = None
    country_name: Optional[str] = None
    address_type: Optional[str] = None  # "current" or "permanent"

class ParsedResume(BaseModel):
    """
    Complete structured data extracted from a resume by the LLM.
    Every field name matches exactly the corresponding DB column name.
    """
    # tbl_cp_student fields
    salutation: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    alt_email: Optional[str] = None
    contact_number: Optional[str] = None
    alt_contact_number: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    date_of_birth: Optional[str] = None  # YYYY-MM-DD
    current_city: Optional[str] = None
    gender: Optional[str] = None

    # Related tables
    school: List[SchoolItem] = []
    education: List[EducationItem] = []
    workexp: List[WorkExpItem] = []
    projects: List[ProjectItem] = []
    skills: List[SkillItem] = []
    languages: List[LanguageItem] = []
    certifications: List[CertificationItem] = []
    interests: List[InterestItem] = []
    addresses: List[AddressItem] = []

class ParseResumeRequest(BaseModel):
    """Request body for /parse/resume endpoint."""
    resume_text: str   # minimum 100 characters

class ParseResumeResponse(BaseModel):
    """Response from /parse/resume endpoint."""
    parsed: ParsedResume
    resume_hash: str   # SHA-256 hash of resume_text
```

### schemas/lookup_schema.py

```python
from pydantic import BaseModel
from typing import Optional

class LookupSkillRequest(BaseModel):
    name: str
    complexity: Optional[str] = "Intermediate"

class LookupSkillResponse(BaseModel):
    skill_id: int
    name: str
    complexity: str
    is_new: bool

class LookupLanguageRequest(BaseModel):
    language_name: str

class LookupLanguageResponse(BaseModel):
    language_id: int
    language_name: str
    language_code: str
    is_new: bool

class LookupInterestRequest(BaseModel):
    name: str

class LookupInterestResponse(BaseModel):
    interest_id: int
    name: str
    is_new: bool

class LookupCertificationRequest(BaseModel):
    certification_name: str
    issuing_organization: str
    certification_type: Optional[str] = "General"
    is_lifetime: Optional[bool] = None

class LookupCertificationResponse(BaseModel):
    certification_id: int
    certification_name: str
    certification_code: str
    issuing_organization: str
    is_new: bool

class LookupCollegeRequest(BaseModel):
    college_name: str

class LookupCollegeResponse(BaseModel):
    college_id: int
    college_name: str
    is_new: bool

class LookupCourseRequest(BaseModel):
    course_name: str
    specialization_name: Optional[str] = "General"

class LookupCourseResponse(BaseModel):
    course_id: int
    course_name: str
    course_code: str
    specialization_name: str
    specialization_code: str
    is_new: bool

class LookupSalutationRequest(BaseModel):
    value: str

class LookupSalutationResponse(BaseModel):
    salutation_id: Optional[int]
    value: str
    found: bool

class LookupPincodeRequest(BaseModel):
    pincode: str

class LookupPincodeResponse(BaseModel):
    pincode_id: Optional[int]
    pincode: str
    found: bool
```

### schemas/student_schema.py

```python
from pydantic import BaseModel
from typing import Optional

class SaveStudentRequest(BaseModel):
    salutation_id: Optional[int] = None
    first_name: str
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str
    alt_email: Optional[str] = None
    contact_number: Optional[str] = None
    alt_contact_number: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    date_of_birth: Optional[str] = None    # YYYY-MM-DD
    current_city: Optional[str] = None
    gender: Optional[str] = None

class SaveStudentResponse(BaseModel):
    student_id: int
    already_exists: bool
```

### schemas/education_schema.py

```python
from pydantic import BaseModel
from typing import Optional

class SaveSchoolRequest(BaseModel):
    student_id: int
    standard: str                          # "10th" or "12th"
    board: Optional[str] = None
    school_name: Optional[str] = None
    percentage: Optional[float] = None
    passing_year: Optional[int] = None

class SaveSchoolResponse(BaseModel):
    school_id: int

class SaveEducationRequest(BaseModel):
    student_id: int
    college_id: int
    course_id: int
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    cgpa: Optional[float] = None
    percentage: Optional[float] = None

class SaveEducationResponse(BaseModel):
    edu_id: int
```

### schemas/workexp_schema.py

```python
from pydantic import BaseModel
from typing import Optional

class SaveWorkExpRequest(BaseModel):
    student_id: int
    company_name: str
    company_location: Optional[str] = None
    designation: Optional[str] = None
    employment_type: Optional[str] = None
    start_date: Optional[str] = None       # YYYY-MM-DD
    end_date: Optional[str] = None         # YYYY-MM-DD — set to None if is_current=True
    is_current: Optional[bool] = None

class SaveWorkExpResponse(BaseModel):
    workexp_id: int
```

### schemas/project_schema.py

```python
from pydantic import BaseModel
from typing import Optional

class SaveProjectRequest(BaseModel):
    student_id: int
    workexp_id: Optional[int] = None
    project_title: str
    project_description: Optional[str] = None
    achievements: Optional[str] = None
    project_start_date: Optional[str] = None   # YYYY-MM-DD
    project_end_date: Optional[str] = None     # YYYY-MM-DD

class SaveProjectResponse(BaseModel):
    project_id: int

class SaveProjectSkillRequest(BaseModel):
    project_id: int
    skill_id: int

class SaveProjectSkillResponse(BaseModel):
    already_exists: bool
```

### schemas/address_schema.py

```python
from pydantic import BaseModel
from typing import Optional

class SaveAddressRequest(BaseModel):
    student_id: int
    address_line_1: str
    address_line_2: Optional[str] = None
    care_of: Optional[str] = None
    landmark: Optional[str] = None
    pincode_id: int                        # already resolved pincode_id, not raw string
    address_type: Optional[str] = "current"

class SaveAddressResponse(BaseModel):
    address_id: int
```

---

## API ENDPOINTS — FULL SPECIFICATION

### GROUP 1: /extract — Text Extraction (no LLM, no DB)

Router file: `routers/extract_router.py`
Service file: `services/extract_service.py`

#### POST /extract/pdf-to-text
- **Purpose**: Extract raw text from a PDF resume file
- **Request**: `multipart/form-data` with field `file` (PDF file)
- **Validations**:
  - `file` must be present
  - Extension must be `.pdf`
  - File size must be ≤ MAX_FILE_SIZE_MB
- **Service function**: `async def extract_text_from_pdf(file_bytes: bytes) -> dict`
- **Logic in service**:
  1. Write file_bytes to a temp file at `/tmp/{uuid4()}.pdf`
  2. Open with `fitz.open(tmp_path)`
  3. Loop all pages: `for page in doc: text += page.get_text("text") + "\n\n"`
  4. Strip whitespace from final text
  5. Delete temp file in `finally` block
  6. If text is empty (scanned PDF) → raise ValueError("PDF has no extractable text. Please use /extract/image-to-text for scanned PDFs.")
  7. Return `{"text": text, "page_count": doc.page_count, "char_count": len(text)}`
- **Success response**:
  ```json
  {
    "success": true,
    "data": { "text": "...", "page_count": 2, "char_count": 3421 }
  }
  ```
- **Error responses**: 400 for missing file, 400 for wrong extension, 413 for too large, 422 for scanned PDF

#### POST /extract/image-to-text
- **Purpose**: Extract raw text from a resume image using OCR
- **Request**: `multipart/form-data` with field `file` (PNG, JPG, JPEG)
- **Validations**: file present, extension in [png, jpg, jpeg], size ≤ MAX_FILE_SIZE_MB
- **Service function**: `async def extract_text_from_image(file_bytes: bytes) -> dict`
- **Logic in service**:
  1. Write to temp file at `/tmp/{uuid4()}.png`
  2. Open with `PIL.Image.open(tmp_path)`
  3. Run `pytesseract.image_to_string(image, lang='eng')`
  4. Strip whitespace
  5. Delete temp file in `finally`
  6. If text is empty → raise ValueError("OCR produced no text. Image may be too blurry or low resolution.")
  7. Return `{"text": text, "char_count": len(text)}`
- **Success response**:
  ```json
  {
    "success": true,
    "data": { "text": "...", "char_count": 2100 }
  }
  ```

---

### GROUP 2: /parse — LLM Parsing (2 LLM calls total, no DB)

Router file: `routers/parse_router.py`
Service file: `services/llm_service.py`

#### POST /parse/resume
- **Purpose**: Send resume text to Claude LLM and get structured JSON back
- **Request body**: `ParseResumeRequest` — field `resume_text: str` (min 100 chars)
- **Service function**: `async def parse_resume_text(resume_text: str) -> ParsedResume`

**Implement these constants at the top of `llm_service.py`:**

```python
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
```

**Implement these functions in `llm_service.py`:**

```python
async def call_llm(system_prompt: str, user_message: str) -> dict:
    """
    Makes one call to the Anthropic Claude API.
    Strips markdown code fences from response before JSON parsing.
    Raises ValueError if response is not valid JSON.
    Returns parsed dict.
    """

async def merge_pass1_and_pass2(pass1: dict, pass2: dict) -> dict:
    """
    Merges two LLM extraction passes.
    For scalar fields: use pass2 value if not null, else keep pass1 value.
    For array fields: use whichever array is longer/more complete.
    Returns merged dict.
    """

async def parse_resume_text(resume_text: str) -> ParsedResume:
    """
    Full two-pass LLM extraction pipeline.
    Pass 1: extract everything.
    Pass 2: find missed data and fix errors.
    Validates that first_name and email are present after merge.
    Returns ParsedResume Pydantic model.
    """
```

**LLM calling code pattern (use exactly this):**
```python
import anthropic
from config import get_settings

settings = get_settings()
client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

response = client.messages.create(
    model=settings.claude_model,
    max_tokens=settings.claude_max_tokens,
    temperature=settings.claude_temperature,
    system=system_prompt,
    messages=[{"role": "user", "content": user_message}]
)
raw_text = response.content[0].text
```

**JSON cleaning pattern (always strip fences before parsing):**
```python
import re, json

def clean_and_parse_json(raw_text: str) -> dict:
    clean = raw_text.strip()
    clean = re.sub(r'^```json\s*', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'^```\s*', '', clean)
    clean = re.sub(r'\s*```$', '', clean)
    return json.loads(clean.strip())
```

- **Success response**:
  ```json
  {
    "success": true,
    "data": {
      "parsed": { "first_name": "Rahul", "email": "rahul@email.com", ... },
      "resume_hash": "abc123def456..."
    }
  }
  ```
- **Error cases**: resume_text too short (<100 chars), LLM API error, JSON parse failed, first_name or email missing from result

---

### GROUP 3: /lookup — Master Table Find or Create

Router file: `routers/lookup_router.py`
Service file: `services/lookup_service.py`

**All lookup endpoints follow this exact pattern:**
1. Query the master table for an existing record using case-insensitive match: `WHERE LOWER(column) = LOWER(:value)`
2. If found → return existing record with `is_new: false`
3. If not found → generate next ID using `SELECT COALESCE(MAX(id_column), 0) + 1`, insert new record, return with `is_new: true`
4. Wrap in try-except — if duplicate key error on insert (race condition) → fetch and return existing

**IMPORTANT about IDs**: All these tables use manual integer IDs (not AUTO_INCREMENT for the business key column). Always use `SELECT COALESCE(MAX(skill_id), 0) + 1 FROM tbl_cp_mskills` pattern via `db.execute(text(...))`.

#### POST /lookup/skill
- **DB table**: `tbl_cp_mskills`
- **Unique match**: `LOWER(name) = LOWER(:name)`
- **Request**: `LookupSkillRequest` — `name: str`, `complexity: str = "Intermediate"`
- **Service function**: `async def find_or_create_skill(db: AsyncSession, name: str, complexity: str) -> LookupSkillResponse`
- **On create**: `language_id` → query `tbl_cp_mlanguages WHERE LOWER(language_name) = 'general'`. If not found, use `language_id = 1`. Set `description = 'No description'`, `version = 'N/A'`, `status = 'Active'`.
- **Response**: `LookupSkillResponse`

#### POST /lookup/language
- **DB table**: `tbl_cp_mlanguages`
- **Unique match**: `LOWER(language_name) = LOWER(:language_name)`
- **Request**: `LookupLanguageRequest` — `language_name: str`
- **Service function**: `async def find_or_create_language(db: AsyncSession, language_name: str) -> LookupLanguageResponse`
- **On create**: generate `language_code` = uppercase of first 3 chars (e.g. "Hindi" → "HIN"). If that code already exists → append "2", "3", etc. until unique.
- **Response**: `LookupLanguageResponse`

#### POST /lookup/interest
- **DB table**: `tbl_cp_minterests`
- **Unique match**: `LOWER(name) = LOWER(:name)`
- **Request**: `LookupInterestRequest` — `name: str`
- **Service function**: `async def find_or_create_interest(db: AsyncSession, name: str) -> LookupInterestResponse`
- **Response**: `LookupInterestResponse`

#### POST /lookup/certification
- **DB table**: `tbl_cp_mcertifications`
- **Unique match**: `LOWER(certification_name) = LOWER(:certification_name) AND LOWER(issuing_organization) = LOWER(:issuing_organization)`
- **Request**: `LookupCertificationRequest`
- **Service function**: `async def find_or_create_certification(db: AsyncSession, ...) -> LookupCertificationResponse`
- **On create**: generate `certification_code`:
  - Take first word of `issuing_organization`, uppercase it (e.g. "Amazon" from "Amazon Web Services" → "AWS")
  - Take first letter of each significant word in `certification_name` (skip "of","the","and","in","for") (e.g. "Certified Cloud Practitioner" → "CCP")
  - Join with "-" → "AWS-CCP"
  - If that code already exists → append `-{certification_id}` to make unique
- **Response**: `LookupCertificationResponse`

#### POST /lookup/college
- **DB table**: `tbl_cp_mcolleges`
- **Unique match**: `LOWER(college_name) = LOWER(:college_name)`
- **Request**: `LookupCollegeRequest` — `college_name: str`
- **Service function**: `async def find_or_create_college(db: AsyncSession, college_name: str) -> LookupCollegeResponse`
- **On create**: set all defaults (spoc, tpo, coordinator names = 'Not Assigned', phones = '0000000000', emails = 'noreply@college.com', priority = 5)
- **Response**: `LookupCollegeResponse` — always return `is_new: true` if created, so admin knows to review

#### POST /lookup/course
- **DB table**: `tbl_cp_mcourses`
- **Unique match**: `LOWER(course_name) = LOWER(:course_name) AND LOWER(specialization_name) = LOWER(:specialization_name)`
- **Request**: `LookupCourseRequest` — `course_name: str`, `specialization_name: str = "General"`
- **Service function**: `async def find_or_create_course(db: AsyncSession, course_name: str, specialization_name: str) -> LookupCourseResponse`
- **On create**: generate codes using this hardcoded mapping dict:
  ```python
  COURSE_CODE_MAP = {
      "bachelor of technology": "BTECH",
      "master of technology": "MTECH",
      "bachelor of engineering": "BE",
      "master of engineering": "ME",
      "bachelor of computer applications": "BCA",
      "master of computer applications": "MCA",
      "bachelor of business administration": "BBA",
      "master of business administration": "MBA",
      "bachelor of science": "BSC",
      "master of science": "MSC",
      "bachelor of commerce": "BCOM",
      "master of commerce": "MCOM",
      "bachelor of arts": "BA",
      "master of arts": "MA",
      "bachelor of computer science": "BCS",
      "doctor of philosophy": "PHD",
      "diploma": "DIP",
      "post graduate diploma": "PGD",
  }
  ```
  If course_name not in map → take first letter of each word (e.g. "Bachelor of Design" → "BD").
  For `specialization_code`: take first letter of each word in specialization_name, uppercase (e.g. "Computer Science" → "CS", "Information Technology" → "IT").
  If generated codes already exist → append numeric suffix.
- **Response**: `LookupCourseResponse`

#### POST /lookup/salutation
- **DB table**: `tbl_cp_msalutation`
- **Unique match**: `LOWER(value) = LOWER(:value)`
- **Request**: `LookupSalutationRequest` — `value: str`
- **Service function**: `async def find_salutation(db: AsyncSession, value: str) -> LookupSalutationResponse`
- **DO NOT create** if not found — salutation is a fixed list. Return `found: false`, `salutation_id: null`.
- **Response**: `LookupSalutationResponse`

#### POST /lookup/pincode
- **DB table**: `tbl_cp_mpincodes`
- **Unique match**: `pincode = :pincode`
- **Request**: `LookupPincodeRequest` — `pincode: str`
- **Service function**: `async def find_pincode(db: AsyncSession, pincode: str) -> LookupPincodeResponse`
- **DO NOT create** if not found — geography is pre-seeded. Return `found: false`, `pincode_id: null`.
- **Response**: `LookupPincodeResponse`

---

### GROUP 4: /save — Database Insert Endpoints (one per entity)

Router file: `routers/save_router.py`
Service file: `services/save_service.py`

Each endpoint inserts exactly one record into exactly one table. These endpoints do NOT call any lookup internally — the caller must pass fully resolved IDs.

**ID generation pattern for ALL save functions:**
```python
result = await db.execute(text("SELECT COALESCE(MAX(student_id), 0) + 1 FROM tbl_cp_student"))
next_id = result.scalar()
```
Use the correct column name per table.

#### POST /save/student
- **DB table**: `tbl_cp_student`
- **Request**: `SaveStudentRequest`
- **Service function**: `async def save_student(db: AsyncSession, data: SaveStudentRequest) -> SaveStudentResponse`
- **Logic**:
  1. Check if student with same `email` exists: `SELECT student_id FROM tbl_cp_student WHERE email = :email`
  2. If exists → return `{"student_id": existing_id, "already_exists": true}`
  3. If not exists:
     - Get next student_id
     - Apply defaults: `date_of_birth = '1900-01-01'` if null, `current_city = 'Not Specified'` if null, `gender = 'Not Specified'` if null, `middle_name = ''` if null, `last_name = ''` if null, `alt_email = ''` if null, `alt_contact_number = '0000000000'` if null, `linkedin_url = ''` if null, `github_url = ''` if null, `portfolio_url = ''` if null, `resume_url = ''`, `profile_photo_url = 'default_profile.png'`, `status = 'Active'`, `user_type = 'Student'`, `is_active = True`
     - Insert
- **Response**: `SaveStudentResponse` — `{"student_id": 101, "already_exists": false}`

#### POST /save/school
- **DB table**: `tbl_cp_student_school`
- **Request**: `SaveSchoolRequest`
- **Service function**: `async def save_school(db: AsyncSession, data: SaveSchoolRequest) -> SaveSchoolResponse`
- **Defaults**: `board = 'Not Specified'`, `school_name = 'Not Specified'`, `percentage = 0.00`, `passing_year = 0`
- **Response**: `SaveSchoolResponse` — `{"school_id": 45}`

#### POST /save/education
- **DB table**: `tbl_cp_student_education`
- **Request**: `SaveEducationRequest` — requires pre-resolved `college_id` and `course_id`
- **Service function**: `async def save_education(db: AsyncSession, data: SaveEducationRequest) -> SaveEducationResponse`
- **Defaults**: `cgpa = 0.00`, `percentage = 0.00`, `start_year = 0`, `end_year = 0`
- **Response**: `SaveEducationResponse` — `{"edu_id": 88}`

#### POST /save/workexp
- **DB table**: `tbl_cp_student_workexp`
- **Request**: `SaveWorkExpRequest`
- **Service function**: `async def save_workexp(db: AsyncSession, data: SaveWorkExpRequest) -> SaveWorkExpResponse`
- **Defaults**: `company_location = 'Not Specified'`, `designation = 'Not Specified'`, `employment_type = 'Full-Time'`
- **Special**: if `is_current = True` → set `end_date = date(1900, 1, 1)` in DB (this is the convention)
- **Special**: if `start_date` is null → set `start_date = date(1900, 1, 1)`
- **Response**: `SaveWorkExpResponse` — `{"workexp_id": 33}`

#### POST /save/project
- **DB table**: `tbl_cp_studentprojects`
- **Request**: `SaveProjectRequest` — `workexp_id` is optional (null if independent project)
- **Service function**: `async def save_project(db: AsyncSession, data: SaveProjectRequest) -> SaveProjectResponse`
- **Defaults**: `project_start_date = date(1900,1,1)`, `project_end_date = date(1900,1,1)` when null
- **Response**: `SaveProjectResponse` — `{"project_id": 77}`

#### POST /save/project-skill
- **DB table**: `tbl_cp_m2m_studentproject_skill`
- **Request**: `SaveProjectSkillRequest` — `project_id: int`, `skill_id: int`
- **Service function**: `async def save_project_skill(db: AsyncSession, project_id: int, skill_id: int) -> SaveProjectSkillResponse`
- **Check duplicate**: if `(project_id, skill_id)` already exists → return `{"already_exists": true}` without error
- **Response**: `SaveProjectSkillResponse` — `{"already_exists": false}`

#### POST /save/student-skill
- **DB table**: `tbl_cp_m2m_std_skill`
- **Request body**: `{"student_id": 101, "skill_id": 12}`
- **Service function**: `async def save_student_skill(db: AsyncSession, student_id: int, skill_id: int)`
- **Check duplicate**: if `(student_id, skill_id)` already exists → return `{"already_exists": true}` without error
- **Response**: `{"already_exists": false}`

#### POST /save/student-language
- **DB table**: `tbl_cp_m2m_std_lng`
- **Request body**: `{"student_id": 101, "language_id": 5}`
- **Service function**: `async def save_student_language(db: AsyncSession, student_id: int, language_id: int)`
- **Check duplicate**: if pair exists → return `{"already_exists": true}`
- **Response**: `{"already_exists": false}`

#### POST /save/student-interest
- **DB table**: `tbl_cp_m2m_std_interest`
- **Request body**: `{"student_id": 101, "interest_id": 8}`
- **Service function**: `async def save_student_interest(db: AsyncSession, student_id: int, interest_id: int)`
- **Check duplicate**: if pair exists → return `{"already_exists": true}`
- **Response**: `{"already_exists": false}`

#### POST /save/student-certification
- **DB table**: `tbl_cp_m2m_student_certification`
- **Request body**:
  ```json
  {
    "student_id": 101,
    "certification_id": 3,
    "issue_date": "2023-01-01",
    "expiry_date": "2026-01-01",
    "certificate_url": "https://credly.com/badges/abc",
    "credential_id": "AWS-CCP-9871"
  }
  ```
- **Service function**: `async def save_student_certification(db: AsyncSession, data: dict)`
- **Defaults**: `issue_date = date(1900,1,1)` if null, `expiry_date = date(9999,12,31)` if null, `certificate_url = ''`, `credential_id = ''`, `is_verified = False`
- **Check duplicate**: if `(student_id, certification_id)` exists → return `{"already_exists": true}`
- **Response**: `{"already_exists": false}`

#### POST /save/address
- **DB table**: `tbl_cp_student_address`
- **Request**: `SaveAddressRequest` — requires pre-resolved `pincode_id`
- **Service function**: `async def save_address(db: AsyncSession, data: SaveAddressRequest) -> SaveAddressResponse`
- **Defaults**: `address_line_2 = ''`, `care_of = ''`, `landmark = 'No Landmark'`, `latitude = 0.0`, `longitude = 0.0`, `address_expiry = date(9999,12,31)`
- **Response**: `SaveAddressResponse` — `{"address_id": 201}`

---

### GROUP 5: /resume — Orchestrator (full pipeline)

Router file: `routers/orchestrator_router.py`
Service file: `services/orchestrator_service.py`

#### POST /resume/upload
- **Purpose**: The ONE endpoint that the client calls to process a full resume. Accepts a file, runs the entire pipeline, fills the DB.
- **Request**: `multipart/form-data` with field `file` (PDF or image)
- **Service function**: `async def run_full_pipeline(db: AsyncSession, file_bytes: bytes, filename: str) -> dict`

**Run these steps in EXACTLY this order. Log each step with step number and name:**

```
STEP 1 — Extract text
  Detect extension from filename.
  If .pdf → call extract_service.extract_text_from_pdf(file_bytes)
  If .png/.jpg/.jpeg → call extract_service.extract_text_from_image(file_bytes)
  If text is empty → raise error, stop.
  Log: "Step 1 complete: extracted {char_count} chars"

STEP 2 — Duplicate check
  Compute SHA-256 hash of resume_text using hash_utils.compute_resume_hash(resume_text)
  Query: SELECT student_id FROM tbl_cp_resume_hashes WHERE hash = :hash
  If found → return immediately:
    {"student_id": existing_student_id, "already_existed": true, "message": "Resume already processed"}
  Log: "Step 2 complete: no duplicate found"

STEP 3 — LLM Parse (2 LLM calls happen here)
  Call llm_service.parse_resume_text(resume_text) → returns ParsedResume
  If fails → raise error, stop. Do not save partial data.
  Log: "Step 3 complete: LLM parsing done"

STEP 4 — Save student core record
  If parsed.salutation is not null:
    Call lookup_service.find_salutation(db, parsed.salutation)
    salutation_id = result.salutation_id if result.found else None
  Else:
    salutation_id = None
  
  Call save_service.save_student(db, SaveStudentRequest(
    salutation_id = salutation_id,
    first_name = parsed.first_name,
    middle_name = parsed.middle_name,
    last_name = parsed.last_name,
    email = parsed.email,
    alt_email = parsed.alt_email,
    contact_number = parsed.contact_number,
    alt_contact_number = parsed.alt_contact_number,
    linkedin_url = parsed.linkedin_url,
    github_url = parsed.github_url,
    portfolio_url = parsed.portfolio_url,
    date_of_birth = parsed.date_of_birth,
    current_city = parsed.current_city,
    gender = parsed.gender
  ))
  
  student_id = result.student_id
  already_existed = result.already_exists
  Log: "Step 4 complete: student_id={student_id}"

STEP 5 — Save school records
  schools_saved = 0
  For each school_item in parsed.school:
    If school_item.standard is null → skip
    Try:
      Call save_service.save_school(db, SaveSchoolRequest(
        student_id = student_id,
        standard = school_item.standard,
        board = school_item.board,
        school_name = school_item.school_name,
        percentage = school_item.percentage,
        passing_year = school_item.passing_year
      ))
      schools_saved += 1
    Except → append to warnings list, continue
  Log: "Step 5 complete: {schools_saved} school records saved"

STEP 6 — Save college education
  educations_saved = 0
  For each edu_item in parsed.education:
    If edu_item.college_name is null OR edu_item.course_name is null → skip
    Try:
      college_result = await lookup_service.find_or_create_college(db, edu_item.college_name)
      college_id = college_result.college_id
      
      course_result = await lookup_service.find_or_create_course(
        db,
        edu_item.course_name,
        edu_item.specialization_name or "General"
      )
      course_id = course_result.course_id
      
      await save_service.save_education(db, SaveEducationRequest(
        student_id = student_id,
        college_id = college_id,
        course_id = course_id,
        start_year = edu_item.start_year,
        end_year = edu_item.end_year,
        cgpa = edu_item.cgpa,
        percentage = edu_item.percentage
      ))
      educations_saved += 1
    Except → append to warnings, continue
  Log: "Step 6 complete: {educations_saved} education records saved"

STEP 7 — Save work experience
  workexp_saved = 0
  workexp_map = {}   # maps company_name (str) → workexp_id (int) for project linking
  For each exp_item in parsed.workexp:
    If exp_item.company_name is null → skip
    Try:
      result = await save_service.save_workexp(db, SaveWorkExpRequest(
        student_id = student_id,
        company_name = exp_item.company_name,
        company_location = exp_item.company_location,
        designation = exp_item.designation,
        employment_type = exp_item.employment_type,
        start_date = exp_item.start_date,
        end_date = exp_item.end_date,
        is_current = exp_item.is_current
      ))
      workexp_map[exp_item.company_name] = result.workexp_id
      workexp_saved += 1
    Except → append to warnings, continue
  Log: "Step 7 complete: {workexp_saved} workexp records saved"

STEP 8 — Save projects + project skills
  projects_saved = 0
  For each proj_item in parsed.projects:
    If proj_item.project_title is null → skip
    Try:
      # Resolve workexp_id using the workexp_map from Step 7
      linked_workexp_id = None
      If proj_item.workexp_company_name is not null:
        linked_workexp_id = workexp_map.get(proj_item.workexp_company_name, None)
      
      proj_result = await save_service.save_project(db, SaveProjectRequest(
        student_id = student_id,
        workexp_id = linked_workexp_id,
        project_title = proj_item.project_title,
        project_description = proj_item.project_description,
        achievements = proj_item.achievements,
        project_start_date = proj_item.project_start_date,
        project_end_date = proj_item.project_end_date
      ))
      project_id = proj_result.project_id
      projects_saved += 1
      
      # Save skills used in this specific project
      For each skill_name in proj_item.skills_used:
        If skill_name is null or empty → skip
        Try:
          skill_result = await lookup_service.find_or_create_skill(db, skill_name, "Intermediate")
          await save_service.save_project_skill(db, project_id, skill_result.skill_id)
        Except → append to warnings, continue
    Except → append to warnings, continue
  Log: "Step 8 complete: {projects_saved} projects saved"

STEP 9 — Save student skills
  skills_saved = 0
  For each skill_item in parsed.skills:
    If skill_item.name is null → skip
    Try:
      skill_result = await lookup_service.find_or_create_skill(
        db, skill_item.name, skill_item.complexity or "Intermediate"
      )
      await save_service.save_student_skill(db, student_id, skill_result.skill_id)
      skills_saved += 1
    Except → append to warnings, continue
  Log: "Step 9 complete: {skills_saved} skills linked to student"

STEP 10 — Save languages
  languages_saved = 0
  For each lang_item in parsed.languages:
    If lang_item.language_name is null → skip
    Try:
      lang_result = await lookup_service.find_or_create_language(db, lang_item.language_name)
      await save_service.save_student_language(db, student_id, lang_result.language_id)
      languages_saved += 1
    Except → append to warnings, continue
  Log: "Step 10 complete: {languages_saved} languages linked"

STEP 11 — Save certifications
  certifications_saved = 0
  For each cert_item in parsed.certifications:
    If cert_item.certification_name is null OR cert_item.issuing_organization is null → skip
    Try:
      cert_result = await lookup_service.find_or_create_certification(
        db,
        cert_item.certification_name,
        cert_item.issuing_organization,
        cert_item.certification_type or "General",
        cert_item.is_lifetime
      )
      await save_service.save_student_certification(db, {
        "student_id": student_id,
        "certification_id": cert_result.certification_id,
        "issue_date": cert_item.issue_date,
        "expiry_date": cert_item.expiry_date,
        "certificate_url": cert_item.certificate_url,
        "credential_id": cert_item.credential_id
      })
      certifications_saved += 1
    Except → append to warnings, continue
  Log: "Step 11 complete: {certifications_saved} certifications saved"

STEP 12 — Save interests (career domain areas)
  interests_saved = 0
  For each interest_item in parsed.interests:
    If interest_item.name is null → skip
    Try:
      interest_result = await lookup_service.find_or_create_interest(db, interest_item.name)
      await save_service.save_student_interest(db, student_id, interest_result.interest_id)
      interests_saved += 1
    Except → append to warnings, continue
  Log: "Step 12 complete: {interests_saved} interests linked"

STEP 13 — Save addresses
  addresses_saved = 0
  For each addr_item in parsed.addresses:
    If addr_item.address_line_1 is null → skip
    If addr_item.pincode is null → skip (cannot save address without pincode_id)
    Try:
      pincode_result = await lookup_service.find_pincode(db, addr_item.pincode)
      If pincode_result.found is False:
        Log WARNING: f"Pincode {addr_item.pincode} not found in tbl_cp_mpincodes. Address skipped."
        append to warnings
        continue
      
      await save_service.save_address(db, SaveAddressRequest(
        student_id = student_id,
        address_line_1 = addr_item.address_line_1,
        address_line_2 = addr_item.address_line_2,
        landmark = addr_item.landmark,
        pincode_id = pincode_result.pincode_id,
        address_type = addr_item.address_type or "current"
      ))
      addresses_saved += 1
    Except → append to warnings, continue
  Log: "Step 13 complete: {addresses_saved} addresses saved"

STEP 14 — Store resume hash
  INSERT INTO tbl_cp_resume_hashes (hash, student_id) VALUES (:hash, :student_id)
  Log: "Step 14 complete: resume hash stored"

STEP 15 — Return final summary
```

- **Success response**:
  ```json
  {
    "success": true,
    "data": {
      "student_id": 101,
      "resume_hash": "abc123...",
      "already_existed": false,
      "summary": {
        "schools_saved": 2,
        "educations_saved": 1,
        "workexps_saved": 1,
        "projects_saved": 3,
        "skills_saved": 8,
        "languages_saved": 2,
        "certifications_saved": 1,
        "interests_saved": 3,
        "addresses_saved": 1
      },
      "warnings": []
    }
  }
  ```
- **Error handling**:
  - If Step 1 (extract) fails → return error immediately, do not proceed
  - If Step 3 (LLM parse) fails → return error immediately, do not proceed
  - If Step 4 (save student) fails → return error immediately, do not proceed
  - Steps 5-13 → on failure of individual item: log warning, append to `warnings[]`, continue with remaining items
  - Always return the full summary even if some steps had warnings

---

## main.py — FULL IMPLEMENTATION

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlalchemy import text
from database import engine, AsyncSessionLocal
from routers.extract_router import router as extract_router
from routers.parse_router import router as parse_router
from routers.lookup_router import router as lookup_router
from routers.save_router import router as save_router
from routers.orchestrator_router import router as orchestrator_router
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup and shutdown."""
    # Startup: create tbl_cp_resume_hashes if not exists
    async with AsyncSessionLocal() as db:
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS tbl_cp_resume_hashes (
                hash       VARCHAR(64)  NOT NULL PRIMARY KEY,
                student_id INT          NOT NULL,
                created_at DATETIME     DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await db.commit()
    logger.info("Startup complete. tbl_cp_resume_hashes ensured.")
    yield
    # Shutdown
    await engine.dispose()
    logger.info("Shutdown complete.")

app = FastAPI(
    title="Resume Parser API",
    description="Automatically fills campus5 database from resume files using LLM parsing.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(extract_router,      prefix="/extract",  tags=["Extract"])
app.include_router(parse_router,        prefix="/parse",    tags=["Parse"])
app.include_router(lookup_router,       prefix="/lookup",   tags=["Lookup"])
app.include_router(save_router,         prefix="/save",     tags=["Save"])
app.include_router(orchestrator_router, prefix="/resume",   tags=["Resume"])

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
```

---

## utils/response_utils.py — FULL IMPLEMENTATION

```python
from fastapi.responses import JSONResponse
from typing import Any, Optional

def success_response(data: Any, status_code: int = 200) -> JSONResponse:
    """Returns standard success JSON response."""
    return JSONResponse(
        status_code=status_code,
        content={"success": True, "data": data}
    )

def error_response(error: str, detail: Optional[str] = None, status_code: int = 400) -> JSONResponse:
    """Returns standard error JSON response."""
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "error": error, "detail": detail}
    )
```

---

## utils/hash_utils.py — FULL IMPLEMENTATION

```python
import hashlib

def compute_resume_hash(resume_text: str) -> str:
    """
    Computes SHA-256 hash of resume text for duplicate detection.
    Text is stripped and encoded to UTF-8 before hashing.
    Returns 64-character hex string.
    """
    return hashlib.sha256(resume_text.strip().encode("utf-8")).hexdigest()
```

---

## utils/date_utils.py — FULL IMPLEMENTATION

```python
from datetime import date, datetime
from typing import Optional

def parse_date_string(date_str: Optional[str]) -> Optional[date]:
    """
    Converts a YYYY-MM-DD string from LLM output to Python date object.
    Returns None if date_str is None or empty.
    Returns date(1900, 1, 1) if parsing fails (safe default for DB).
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m").date()
        except ValueError:
            return date(1900, 1, 1)

def safe_date(date_str: Optional[str], default: date = date(1900, 1, 1)) -> date:
    """
    Same as parse_date_string but always returns a date — never None.
    Uses provided default if parsing fails or input is null.
    """
    result = parse_date_string(date_str)
    return result if result is not None else default
```

---

## requirements.txt

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
sqlalchemy==2.0.30
aiomysql==0.2.0
pymysql==1.1.1
pydantic==2.7.1
pydantic-settings==2.3.1
anthropic==0.28.0
python-dotenv==1.0.1
pymupdf==1.24.5
pillow==10.3.0
pytesseract==0.3.10
python-multipart==0.0.9
cryptography==42.0.8
```

---

## GLOBAL RULES FOR ALL ROUTER FILES

Every router file must follow this exact pattern:

```python
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from schemas.common_schema import SuccessResponse, ErrorResponse
from utils.response_utils import success_response, error_response
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/endpoint-name",
    response_model=SuccessResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def endpoint_function(
    request: RequestSchema,
    db: AsyncSession = Depends(get_db)
):
    """Docstring explaining what this endpoint does."""
    try:
        result = await some_service.some_function(db, ...)
        return success_response(result.model_dump())
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"Unexpected error in /endpoint-name: {e}")
        return error_response("Internal server error", detail=str(e), status_code=500)
```

---

## GLOBAL RULES FOR ALL SERVICE FILES

Every service file must follow these rules:

1. No FastAPI imports. No router imports. Pure async Python.
2. All functions are `async def`.
3. All DB operations use `await db.execute(text("..."), {"param": value})` for raw SQL OR SQLAlchemy ORM `await db.get(Model, id)`.
4. Never use string formatting to build SQL queries (SQL injection risk). Always use SQLAlchemy `text()` with parameter binding.
5. Every function has a full docstring.
6. Log start of each major operation at DEBUG level.
7. Let exceptions propagate to the router — do not swallow exceptions in services.

---

## WHAT NOT TO DO — COPILOT MUST NEVER DO THESE

1. Do NOT use Flask. Only FastAPI.
2. Do NOT call the LLM more than 2 times per resume.
3. Do NOT use AUTO_INCREMENT for business key ID columns. Use `COALESCE(MAX(id), 0) + 1`.
4. Do NOT put business logic in router files. Routers only call services.
5. Do NOT hardcode any API keys, passwords, or database credentials in code.
6. Do NOT return HTML from any endpoint. Only JSON.
7. Do NOT use synchronous DB drivers with async code. Use `aiomysql` not `pymysql` for async.
8. Do NOT skip docstrings on any function or class.
9. Do NOT let any unhandled exception return a non-JSON response to the client.
10. Do NOT create or modify any DB tables except `tbl_cp_resume_hashes`. All other tables already exist.
11. Do NOT insert into `tbl_cp_mpincodes`, `tbl_cp_mcities`, `tbl_cp_mstates`, or `tbl_cp_mcountries`. These are read-only.
12. Do NOT insert into `tbl_cp_msalutation`. It is read-only.
13. Do NOT use SQLite. Only MySQL with aiomysql.
14. Do NOT import from `main.py` in any other file (circular import risk).
15. Do NOT use `response_model` that doesn't match the actual returned data shape.

---

*End of prompt. Build the complete project exactly as described above, file by file.*