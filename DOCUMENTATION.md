# Resume Parser - Flask Project Documentation

## Project Overview

**Resume Parser** is an async FastAPI application designed to extract and parse resume data using Google Gemini API. The application processes PDF and DOCX files, extracts structured information about candidates, and stores it in a MySQL database.

**Technology Stack:**
- **Framework:** FastAPI 0.135.1 with Uvicorn
- **Language:** Python 3.13.7
- **Database:** MySQL with SQLAlchemy 2.0.48 async ORM and aiomysql 0.3.2
- **LLM:** Google Gemini API (gemini-1.5-flash model)
- **File Processing:** PyMuPDF 1.27.2.2 (PDF), python-docx 1.2.0 (DOCX)
- **Configuration:** Pydantic-settings 2.13.1 with .env file-based config

---

## Project Structure

```
RP_flask/
├── main.py                 # FastAPI application entry point
├── config.py               # Pydantic Settings configuration
├── database.py             # Database connection and session management
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (API keys, database credentials)
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
│
├── models/                 # SQLAlchemy ORM models
│   ├── __init__.py
│   ├── student_model.py    # Student entity (primary)
│   ├── education_model.py  # Education entries
│   ├── workexp_model.py    # Work experience entries
│   ├── project_model.py    # Project entries
│   ├── address_model.py    # Address information
│   ├── master_model.py     # Master data relationships
│   └── m2m_model.py        # Many-to-many relationship model
│
├── schemas/                # Pydantic schemas for request/response validation
│   ├── __init__.py
│   ├── student_schema.py   # Student DTO
│   ├── education_schema.py # Education DTO
│   ├── workexp_schema.py   # Work experience DTO
│   ├── project_schema.py   # Project DTO
│   ├── address_schema.py   # Address DTO
│   ├── common_schema.py    # Shared schema components
│   ├── extract_schema.py   # Resume extraction request/response schemas
│   ├── parse_schema.py     # Text parsing schemas
│   └── lookup_schema.py    # Lookup operation schemas
│
├── services/               # Business logic layer
│   ├── __init__.py
│   ├── llm_service.py      # Google Gemini API integration (core LLM operations)
│   ├── extract_service.py  # Resume file extraction and processing
│   ├── parse_service.py    # Resume text parsing pipeline
│   ├── lookup_service.py   # Database lookup operations
│   ├── save_service.py     # Database persistence operations
│   └── orchestrator_service.py # Workflow orchestration
│
├── routers/                # FastAPI route handlers
│   ├── __init__.py
│   ├── extract_router.py   # File upload and extraction endpoints
│   ├── parse_router.py     # Text parsing endpoints
│   ├── lookup_router.py    # Data lookup endpoints
│   ├── save_router.py      # Data persistence endpoints
│   └── orchestrator_router.py # Workflow orchestration endpoints
│
├── utils/                  # Utility functions
│   ├── __init__.py
│   ├── cache_utils.py      # Resume caching logic (hashing, storage)
│   ├── date_utils.py       # Date parsing and normalization
│   ├── hash_utils.py       # Hashing utilities
│   └── response_utils.py   # Response formatting helpers
│
└── resume_cache/           # Temporary storage for parsed resume JSON files
    ├── *.json              # Parsed resume data cache
    └── *_meta.json         # Cache metadata files
```

---

## Database Schema

### Core Tables

**students**
- Stores candidate profile information (name, email, phone, etc.)
- Primary entity linking to all other data

**education**
- Education history linked to students
- Fields: degree, institution, field of study, graduation date

**workexperience**
- Work history linked to students
- Fields: job title, company, duration, responsibilities

**projects**
- Project portfolio linked to students
- Fields: project name, description, technologies, duration

**addresses**
- Location information linked to students
- Fields: street, city, state, country, postal code

**master_data**
- Metadata and control table for data versioning

**student_m2m_mapping**
- Many-to-many relationship junction table

---

## API Endpoints

### Extract Router (`/extract`)
- **POST /extract** - Upload resume file (PDF/DOCX) for extraction

### Parse Router (`/parse`)
- **POST /parse** - Parse resume text directly

### Lookup Router (`/lookup`)
- **GET /lookup/{student_id}** - Retrieve student data
- **GET /lookup/all** - List all students
- **POST /lookup/search** - Search students by criteria

### Save Router (`/save`)
- **POST /save** - Save extracted resume data to database
- **PUT /save/{student_id}** - Update existing student record
- **DELETE /save/{student_id}** - Delete student record

### Orchestrator Router (`/orchestrate`)
- **POST /orchestrate** - End-to-end workflow (extract → parse → save)

---

## LLM Integration

### Google Gemini API

**Model:** `gemini-1.5-flash`

**Two-Pass Extraction Pipeline:**
1. **Pass 1 (Full Extraction):** Prompt Gemini to extract all resume information at once
2. **Pass 2 (Gap Check):** Analyze extracted data for missing fields and re-prompt for specific sections

**Features:**
- Asynchronous API calls using `asyncio.to_thread()` for non-blocking operations
- Automatic JSON parsing and error recovery
- Structured output with field type normalization
- Comprehensive error logging and timing metrics

**Configuration:**
```python
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

---

## Setup Instructions

### 1. Prerequisites
- Python 3.13.7 or higher
- MySQL 8.0 or higher
- Google Gemini API key

### 2. Environment Setup

Clone the repository and navigate to the project directory:
```bash
cd RP_flask
```

Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and update with your credentials:
```bash
cp .env.example .env
```

Edit `.env` with:
```
GEMINI_API_KEY=your_actual_gemini_api_key_here
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=campus5
```

### 5. Database Setup

Ensure MySQL is running and create the database:
```sql
CREATE DATABASE IF NOT EXISTS campus5;
```

The application will automatically create tables on first run using SQLAlchemy ORM models.

### 6. Run the Application

```bash
python main.py
```

The server will start on `http://localhost:8000`

### 7. Access API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Performance Notes

### Resume Caching
- Parsed resume JSON files are cached in `resume_cache/` directory
- Cache uses SHA256 hashing of resume text for fast lookups
- Reduces redundant LLM API calls and improves response times

### Async Architecture
- All database operations are async-first using SQLAlchemy 2.0 async sessions
- LLM calls use `asyncio.to_thread()` to prevent event loop blocking
- FastAPI handles concurrent requests efficiently with Uvicorn

### Two-Pass LLM Strategy
- First pass ensures comprehensive extraction of all available data
- Second pass targets specific missing fields identified in Pass 1
- Improves data completeness while controlling API usage

---

## Key Services

### llm_service.py
Core LLM integration handling all Gemini API interactions:
- `parse_resume_text()` - Main entry point for resume parsing with two-pass pipeline
- `call_llm()` - Direct Gemini API calls with structured prompts
- `clean_and_parse_json()` - JSON extraction from markdown code blocks
- `merge_pass1_and_pass2()` - Intelligent merging of extraction results
- `normalize_merged()` - Field type validation and normalization

### extract_service.py
File processing and text extraction:
- PDF extraction using PyMuPDF
- DOCX extraction using python-docx
- File validation and error handling

### orchestrator_service.py
Workflow coordination:
- Orchestrates extract → parse → save pipeline
- Transaction management and error recovery
- Logging and metrics collection

### save_service.py
Database persistence layer:
- Async database operations
- Transaction handling
- Relationship management between entities

---

## Configuration Reference

All application settings are in `config.py` using Pydantic Settings:

```python
class Settings(BaseSettings):
    # LLM Configuration
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    
    # Database Configuration
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "campus5"
    
    # Application Configuration
    app_env: str = "development"
    app_port: int = 8000
    max_file_size_mb: int = 50
    allowed_extensions: list = [".pdf", ".docx"]
```

---

## Error Handling

The application implements comprehensive error handling:
- **File Validation:** Checks file type, size, and format before processing
- **LLM Errors:** Retries and graceful degradation on API failures
- **Database Errors:** Transaction rollback and error logging
- **JSON Parsing:** Markdown code block extraction and fallback parsing

---

## Development Notes

### Adding New Fields to Resume Parsing
1. Update corresponding `*_model.py` in `models/`
2. Update `*_schema.py` in `schemas/`
3. Modify LLM prompts in `llm_service.py`
4. Update database schema if needed

### Testing Resume Parsing
1. Use Swagger UI at `/docs` to upload test resume
2. Check `resume_cache/` for cached results
3. Query `/lookup/{student_id}` to verify database storage

### Debugging
- Enable debug logging in `config.py` (set `app_env=development`)
- Check application logs for LLM API call details and timing
- Monitor database queries using MySQL slow query log

---

## License & Attribution

**Project:** Resume Parser - Resume Data Extraction System
**Organization:** Artiset Internship Program
**Last Updated:** 2025

---

For issues, questions, or contributions, please refer to the project repository or contact the development team.
