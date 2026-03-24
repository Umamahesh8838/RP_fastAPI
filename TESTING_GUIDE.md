# Testing Guide: Two-Step Resume Upload Flow

## Quick Start

### Server Status
✅ **FastAPI Server:** Running on `http://localhost:8080`
✅ **Swagger UI:** Available at `http://localhost:8080/docs`
✅ **ReDoc:** Available at `http://localhost:8080/redoc`
✅ **OpenAPI Schema:** Available at `http://localhost:8080/openapi.json`

### Registered Endpoints
- **POST** `/resume/upload` - One-step upload (existing)
- **POST** `/resume/parse-preview` - Preview parsing (NEW)
- **POST** `/resume/save-confirmed` - Save confirmed (NEW)

---

## Testing via Swagger UI

### Method 1: Using Browser Swagger UI

1. **Open Swagger UI**
   - Navigate to: `http://localhost:8080/docs`
   - All three endpoints will be visible in the interface

2. **Test `/resume/parse-preview`**
   - Click on the endpoint
   - Click "Try it out"
   - Upload a resume file (PDF or DOCX)
   - Click "Execute"
   - Note the `resume_hash` from the response

3. **Test `/resume/save-confirmed`**
   - Click on the endpoint
   - Click "Try it out"
   - Paste this in the request body (update with real data from parse-preview):
   ```json
   {
     "resume_hash": "copy_from_parse_preview_response",
     "parsed": {
       "salutation": "Mr.",
       "first_name": "John",
       "middle_name": "Doe",
       "last_name": "Smith",
       "email": "john@example.com",
       "alt_email": null,
       "contact_number": "9876543210",
       "alt_contact_number": null,
       "linkedin_url": "https://linkedin.com/in/johnsmith",
       "github_url": "https://github.com/johnsmith",
       "portfolio_url": null,
       "date_of_birth": null,
       "current_city": "Bangalore",
       "gender": null,
       "school": [],
       "education": [],
       "workexp": [],
       "projects": [],
       "skills": [],
       "languages": [],
       "certifications": [],
       "interests": [],
       "addresses": []
     }
   }
   ```
   - Click "Execute"
   - Verify response includes `student_id` and `summary`

---

## Testing via cURL

### 1. Test Parse-Preview Endpoint

```bash
# Upload resume and get preview
curl -X POST "http://localhost:8080/resume/parse-preview" \
  -H "accept: application/json" \
  -F "file=@/path/to/resume.pdf"
```

**Expected Response (Success):**
```json
{
  "success": true,
  "data": {
    "resume_hash": "abc123...",
    "already_exists": false,
    "parsed": {
      "first_name": "John",
      "last_name": "Doe",
      ...
    }
  }
}
```

**Expected Response (Duplicate):**
```json
{
  "success": true,
  "data": {
    "resume_hash": "abc123...",
    "already_exists": true,
    "parsed": {
      "first_name": "John",
      "last_name": "Doe",
      ...
    }
  }
}
```

**Error Response (Invalid File):**
```json
{
  "success": false,
  "error": "Unsupported file type",
  "detail": "Allowed types: pdf, docx",
  "status_code": 400
}
```

### 2. Test Save-Confirmed Endpoint

```bash
# Save the confirmed resume
curl -X POST "http://localhost:8080/resume/save-confirmed" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_hash": "abc123...",
    "parsed": {
      "salutation": "Mr.",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com",
      ...rest of fields...
    }
  }'
```

**Expected Response (Success):**
```json
{
  "success": true,
  "data": {
    "student_id": 12345,
    "resume_hash": "abc123...",
    "already_existed": false,
    "summary": {
      "schools_saved": 1,
      "educations_saved": 1,
      "workexps_saved": 2,
      "projects_saved": 1,
      "skills_saved": 5,
      "languages_saved": 2,
      "certifications_saved": 0,
      "interests_saved": 3,
      "addresses_saved": 1
    },
    "warnings": []
  }
}
```

**Error Response (Invalid Data):**
```json
{
  "success": false,
  "error": "resume_hash is required",
  "status_code": 400
}
```

---

## Testing via Python

### Simple Python Test Script

```python
import requests
import json

BASE_URL = "http://localhost:8080"

# Step 1: Parse preview
print("=== Step 1: Parse Preview ===")
with open("resume.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(f"{BASE_URL}/resume/parse-preview", files=files)
    
result = response.json()
print(json.dumps(result, indent=2))

if not result.get("success"):
    print("Parse preview failed!")
    exit(1)

resume_hash = result["data"]["resume_hash"]
parsed_data = result["data"]["parsed"]
already_exists = result["data"]["already_exists"]

print(f"\nResume Hash: {resume_hash}")
print(f"Already Exists: {already_exists}")

# Step 2: Save confirmed (if not duplicate)
if not already_exists:
    print("\n=== Step 2: Save Confirmed ===")
    save_payload = {
        "resume_hash": resume_hash,
        "parsed": parsed_data
    }
    
    response = requests.post(
        f"{BASE_URL}/resume/save-confirmed",
        json=save_payload
    )
    
    result = response.json()
    print(json.dumps(result, indent=2))
    
    if result.get("success"):
        student_id = result["data"]["student_id"]
        print(f"\n✅ Success! Student ID: {student_id}")
    else:
        print("❌ Save failed!")
```

---

## Testing Scenarios

### Scenario 1: New Resume Upload

**Steps:**
1. Call `/resume/parse-preview` with new resume
   - ✅ `already_exists` should be `false`
   - ✅ `parsed` data should be populated
   
2. Call `/resume/save-confirmed` with parsed data
   - ✅ `student_id` should be generated
   - ✅ `already_existed` should be `false`
   - ✅ `summary` should show records saved
   - ✅ Database should have new student record

### Scenario 2: Duplicate Resume

**Steps:**
1. Upload same resume twice via `/resume/parse-preview`
   - First: `already_exists` = `false`
   - Second: `already_exists` = `true` (same hash)
   
2. Parsed data should be identical for both
   - User can choose whether to save duplicate or not

### Scenario 3: Resume Editing

**Steps:**
1. Get parsed data from `/resume/parse-preview`
2. Edit parsed data in frontend (e.g., fix name, add skills)
3. Send edited `ParsedResume` to `/resume/save-confirmed`
   - ✅ Updated data should be saved
   - ✅ Original `resume_hash` used for deduplication

### Scenario 4: Error Handling

**Test Invalid File:**
```bash
curl -X POST "http://localhost:8080/resume/parse-preview" \
  -F "file=@/path/to/file.txt"
# Expected: 400 error "Unsupported file type"
```

**Test File Too Large:**
```bash
# Upload file > max_file_size_mb
# Expected: 413 error "File too large"
```

**Test Missing Data:**
```bash
curl -X POST "http://localhost:8080/resume/save-confirmed" \
  -H "Content-Type: application/json" \
  -d '{"parsed": {}}'
# Expected: 400 error "resume_hash is required"
```

---

## Response Structure

### Success Response Format
```json
{
  "success": true,
  "data": {
    // Endpoint-specific data
  }
}
```

### Error Response Format
```json
{
  "success": false,
  "error": "Error message",
  "detail": "Additional details (optional)",
  "status_code": 400
}
```

---

## Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK - Success | Endpoint executed successfully |
| 400 | Bad Request | Invalid file type, missing fields |
| 413 | Payload Too Large | File exceeds size limit |
| 500 | Internal Server Error | Unexpected server error |

---

## Debugging Tips

### 1. Check Server Logs
- Server logs show detailed step-by-step progression
- Look for "STEP X complete" messages
- Look for "ERROR" or "WARNING" messages

### 2. Enable Debug Mode
- Set log level to DEBUG to see more details
- Check database queries in MySQL logs

### 3. Verify Database State
```sql
-- Check if student was created
SELECT * FROM tbl_cp_student WHERE first_name = 'John';

-- Check resume hashes
SELECT * FROM tbl_cp_resume_hashes;

-- Check work experience
SELECT * FROM tbl_cp_workexp WHERE student_id = 123;
```

### 4. Common Issues

**Issue:** "Ollama API error: llama runner process has terminated"
- **Cause:** Ollama server crashed or ran out of memory
- **Fix:** Restart Ollama server
- **Command:** `ollama serve`

**Issue:** "Document closed" error
- **Cause:** PDF extraction error (already fixed)
- **Status:** ✅ RESOLVED

**Issue:** "CORS error" from browser
- **Cause:** Cross-origin request blocked
- **Status:** ✅ RESOLVED (CORS enabled)

**Issue:** "module 'fitz' has no attribute 'FileError'"
- **Cause:** PyMuPDF exception handling error (already fixed)
- **Status:** ✅ RESOLVED

---

## Performance Testing

### Load Testing One-Step Upload
```bash
# Test existing /resume/upload endpoint
for i in {1..10}; do
  curl -X POST "http://localhost:8080/resume/upload" \
    -F "file=@resume_$i.pdf" &
done
wait
```

### Load Testing Two-Step Flow
```bash
# Test parse-preview endpoint
for i in {1..10}; do
  curl -X POST "http://localhost:8080/resume/parse-preview" \
    -F "file=@resume_$i.pdf" &
done
wait
```

---

## Validation Checklist

### Endpoint Registration
- [ ] `/resume/upload` shows in Swagger UI
- [ ] `/resume/parse-preview` shows in Swagger UI
- [ ] `/resume/save-confirmed` shows in Swagger UI

### Parse-Preview Functionality
- [ ] Accepts PDF files
- [ ] Accepts DOCX files
- [ ] Rejects other file types
- [ ] Rejects files over size limit
- [ ] Returns resume_hash
- [ ] Returns already_exists flag
- [ ] Returns parsed data
- [ ] Does NOT create database records

### Save-Confirmed Functionality
- [ ] Accepts SaveConfirmedRequest JSON
- [ ] Validates resume_hash field
- [ ] Validates parsed field
- [ ] Creates student record
- [ ] Creates related records
- [ ] Stores resume hash
- [ ] Returns student_id
- [ ] Returns summary with counts
- [ ] Returns warnings if any

### Error Handling
- [ ] Invalid file type returns 400
- [ ] File too large returns 413
- [ ] Missing resume_hash returns 400
- [ ] Missing parsed data returns 400
- [ ] Server errors return 500

### Database Integrity
- [ ] Student records created correctly
- [ ] Related records linked properly
- [ ] Resume hashes stored
- [ ] Duplicate detection works
- [ ] No orphaned records created

---

## Production Deployment

### Pre-Deployment Checklist
- [ ] All tests passing
- [ ] Error handling verified
- [ ] Database connectivity confirmed
- [ ] Ollama service running
- [ ] File size limits configured
- [ ] Logging configured
- [ ] CORS configured appropriately
- [ ] Rate limiting configured (if needed)

### Monitoring Points
- Monitor server logs for errors
- Monitor Ollama memory usage
- Monitor database query performance
- Track endpoint response times
- Monitor file upload success rates

### Rollback Plan
1. Restore previous main.py (remove CORS if needed)
2. Restore previous orchestrator_router.py
3. Restore previous orchestrator_service.py
4. Restart FastAPI server
5. Existing `/resume/upload` will still work

---

## Next Steps

1. **Manual Testing** - Test all scenarios locally first
2. **Load Testing** - Test with multiple concurrent requests
3. **Database Testing** - Verify data integrity
4. **Frontend Integration** - Build UI for two-step flow
5. **Production Deployment** - Deploy to production server

---

**Last Updated:** [Current Date]
**Status:** ✅ READY FOR TESTING
