# Quick Start Guide - Resume Parser API

## 📋 Prerequisites Checklist

Before starting, ensure you have:
- [ ] Python 3.8 or higher installed
- [ ] MySQL 5.7+ server running
- [ ] Ollama installed with llama3.1 model
- [ ] campus5 database created with all required tables

## 🚀 Step-by-Step Setup

### Step 1: Install Dependencies

```bash
# Navigate to project directory
cd "c:\Users\HP\OneDrive\Desktop\Artiset internship\RP_flask"

# Create virtual environment (optional but recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
# Copy the template
cp .env.example .env

# Edit .env with your settings:
# - OLLAMA_MODEL: "llama3.1" (default)
# - OLLAMA_BASE_URL: "http://localhost:11434" (default)
# - DB_HOST, DB_PORT, DB_USER, DB_PASSWORD: Your MySQL credentials
# - DB_NAME: Set to "campus5"
```

### Step 3: Ensure Ollama is Running

```bash
# In a separate terminal, start Ollama server
ollama serve

# In another terminal, pull the model (if not already pulled)
ollama pull llama3.1
```

### Step 4: Start the API Server

```bash
# Development mode (with auto-reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Step 5: Access the API

Once running, visit:
- **Interactive Docs (Swagger UI)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **API Root**: http://localhost:8000/

## 📁 Project Structure

```
resume_parser/
├── main.py                    # FastAPI app
├── config.py                  # Settings
├── database.py                # DB setup
├── requirements.txt           # Dependencies
├── .env.example               # Template
├── .env                       # Your config (create from template)
│
├── models/                    # SQLAlchemy ORM
│   ├── student_model.py
│   ├── education_model.py
│   ├── workexp_model.py
│   ├── project_model.py
│   ├── master_model.py
│   ├── address_model.py
│   └── m2m_model.py
│
├── schemas/                   # Pydantic models
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
├── routers/                   # API endpoints
│   ├── extract_router.py
│   ├── parse_router.py
│   ├── lookup_router.py
│   ├── save_router.py
│   └── orchestrator_router.py
│
├── services/                  # Business logic
│   ├── extract_service.py
│   ├── llm_service.py
│   ├── lookup_service.py
│   ├── save_service.py
│   └── orchestrator_service.py
│
└── utils/                     # Helpers
    ├── response_utils.py
    ├── hash_utils.py
    └── date_utils.py
```

## 🧪 Testing the API

### Test 1: Health Check
```bash
curl http://localhost:8000/health
```

### Test 2: Extract PDF Text
```bash
curl -X POST "http://localhost:8000/extract/pdf-to-text" \
  -F "file=@resume.pdf"
```

### Test 3: Extract Image Text
```bash
curl -X POST "http://localhost:8000/extract/image-to-text" \
  -F "file=@resume.png"
```

### Test 4: Parse Resume (LLM)
```bash
curl -X POST "http://localhost:8000/parse/resume" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Your resume text here..."
  }'
```

### Test 5: Full Pipeline
```bash
curl -X POST "http://localhost:8000/resume/upload" \
  -F "file=@resume.pdf"
```

## 🛠️ API Endpoints Overview

### Extract Group
- `POST /extract/pdf-to-text` - Extract text from PDF
- `POST /extract/docx-to-text` - Extract text from Word document

### Parse Group
- `POST /parse/resume` - Parse resume with LLM (2 passes)

### Lookup Group
- `POST /lookup/skill` - Find/create skill
- `POST /lookup/language` - Find/create language
- `POST /lookup/interest` - Find/create interest
- `POST /lookup/certification` - Find/create certification
- `POST /lookup/college` - Find/create college
- `POST /lookup/course` - Find/create course
- `POST /lookup/salutation` - Find salutation (read-only)
- `POST /lookup/pincode` - Find pincode (read-only)

### Save Group
- `POST /save/student` - Save student
- `POST /save/school` - Save school
- `POST /save/education` - Save education
- `POST /save/workexp` - Save work experience
- `POST /save/project` - Save project
- `POST /save/project-skill` - Link project to skill
- `POST /save/student-skill` - Link student to skill
- `POST /save/student-language` - Link student to language
- `POST /save/student-interest` - Link student to interest
- `POST /save/student-certification` - Link student to certification
- `POST /save/address` - Save address

### Resume Group (Full Pipeline)
- `POST /resume/upload` - Upload resume (PDF or DOCX) and process completely

## ⚙️ Configuration Options

In `.env`:

```env
# Ollama Local LLM
OLLAMA_MODEL=llama3.1
OLLAMA_BASE_URL=http://localhost:11434

# MySQL Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=campus5

# Application
APP_ENV=development
APP_PORT=8000
MAX_FILE_SIZE_MB=10
ALLOWED_EXTENSIONS=pdf,docx
```

## 🔧 Troubleshooting

### Issue: "ModuleNotFoundError" when running
**Solution**: Install dependencies first
```bash
pip install -r requirements.txt
```

### Issue: "Connection refused" to MySQL
**Solution**: Check MySQL is running and credentials in .env are correct
```bash
# Test connection
mysql -h localhost -u root -p
```

### Issue: Tesseract not found
**Solution**: Install Tesseract from https://github.com/UB-Mannheim/tesseract/wiki
Then update pytesseract path if needed in utils or environment

### Issue: "API key not valid"
**Solution**: Verify ANTHROPIC_API_KEY in .env is correct
Get key from: https://console.anthropic.com/account/keys

### Issue: Database tables don't exist
**Solution**: Create tables using provided SQL scripts or ORM
The API assumes all tables already exist in the campus5 database

## 📚 Key Features

✅ **PDF & DOCX Extraction** - PyMuPDF + python-docx
✅ **LLM Parsing** - Dual-pass Ollama extraction + gap checking
✅ **Database Integration** - SQLAlchemy async with MySQL
✅ **Master Data Management** - Automatic find-or-create for lookups
✅ **Duplicate Detection** - SHA-256 hashing prevents duplicates
✅ **Error Handling** - Consistent JSON error responses
✅ **Comprehensive Logging** - INFO-level operation tracking
✅ **API Documentation** - Auto-generated Swagger + ReDoc
✅ **Async/Await** - Non-blocking I/O throughout

## 📖 Documentation

- **API Docs** (Swagger UI): Available at `/docs` after running
- **Alternative Docs** (ReDoc): Available at `/redoc`
- **Code Comments**: Every function has docstrings
- **README.md**: Comprehensive project documentation

## ✨ Next Steps

1. ✅ Install dependencies
2. ✅ Configure .env file
3. ✅ Start the server: `uvicorn main:app --reload`
4. ✅ Visit http://localhost:8000/docs
5. ✅ Test endpoints with sample resume
6. ✅ Monitor logs in console

## 📞 Support

For issues or questions:
1. Check the README.md for detailed documentation
2. Review endpoint documentation in Swagger UI
3. Check logs in console for error details
4. Verify .env configuration
5. Ensure all database tables exist

---

**Version**: 1.0.0  
**Last Updated**: March 21, 2026  
**Project**: Artiset Internship - Resume Parser
