# Quick Reference: Two-Step Resume Upload API

## Server Info
- **URL:** `http://localhost:8080`
- **Swagger UI:** `http://localhost:8080/docs`
- **ReDoc:** `http://localhost:8080/redoc`
- **Status:** ✅ Running

---

## Quick Start: Test It Now

### Option 1: Use Swagger UI (Easiest)
1. Go to `http://localhost:8080/docs`
2. Find `/resume/parse-preview`
3. Click "Try it out"
4. Upload a PDF resume
5. Click "Execute"
6. ✅ Done! You'll see the parsed data

### Option 2: Use cURL (Terminal)
```bash
# Parse preview
curl -X POST "http://localhost:8080/resume/parse-preview" \
  -F "file=@your_resume.pdf"

# Save confirmed (use response from above)
curl -X POST "http://localhost:8080/resume/save-confirmed" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_hash": "copy_from_above",
    "parsed": {copy all parsed data from above}
  }'
```

---

## Three Endpoints

### 1. Upload Resume (One-Step - Existing)
```
POST /resume/upload
Content-Type: multipart/form-data

Response: {student_id, resume_hash, summary}
```

### 2. Parse Preview (New - Step 1)
```
POST /resume/parse-preview
Content-Type: multipart/form-data

Response: {resume_hash, already_exists, parsed}
⚠️ Does NOT save to database
```

### 3. Save Confirmed (New - Step 2)
```
POST /resume/save-confirmed
Content-Type: application/json

Body: {resume_hash, parsed}
Response: {student_id, resume_hash, summary}
```

---

## Response Examples

### Parse Preview Success
```json
{
  "success": true,
  "data": {
    "resume_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "already_exists": false,
    "parsed": {
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com",
      ...
    }
  }
}
```

### Save Confirmed Success
```json
{
  "success": true,
  "data": {
    "student_id": 12345,
    "resume_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
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

### Error Response
```json
{
  "success": false,
  "error": "Unsupported file type",
  "detail": "Allowed types: pdf, docx",
  "status_code": 400
}
```

---

## Usage Flow

### Two-Step Flow (User Review)
```
User selects resume file
        ↓
POST /resume/parse-preview
        ↓
Get preview + resume_hash
        ↓
User reviews/edits in UI
        ↓
POST /resume/save-confirmed
        ↓
Student record created
```

### One-Step Flow (Batch Processing)
```
User selects resume file
        ↓
POST /resume/upload
        ↓
Directly create student record
```

---

## Important Notes

✅ **Parse-Preview Does NOT Save**
- Safe to call multiple times
- Safe to cancel anytime
- Use for previewing data

✅ **Save-Confirmed Saves Everything**
- Creates student record
- Creates all related records
- Stores resume hash for deduplication
- Returns student_id for reference

✅ **Duplicate Detection**
- Parse-preview shows `already_exists` flag
- Same resume file = same hash
- User chooses whether to save duplicate or not

✅ **Error Handling**
- File type validation (PDF, DOCX only)
- File size validation
- Input data validation
- User-friendly error messages

---

## File Limits
- **Supported Types:** PDF, DOCX
- **Max Size:** Check config (typically 50MB)
- **Allowed:** All resumes

---

## Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success - Operation completed |
| 400 | Bad Request - Invalid input |
| 413 | File Too Large - Exceeds size limit |
| 500 | Server Error - Unexpected issue |

---

## Testing Checklist

- [ ] Parse-preview with PDF ✓
- [ ] Parse-preview with DOCX ✓
- [ ] Save-confirmed with parsed data ✓
- [ ] Verify student created in database ✓
- [ ] Test duplicate detection ✓
- [ ] Test error scenarios ✓
- [ ] Check Swagger UI documentation ✓

---

## Troubleshooting

**Q: Parse-preview returns error**
- Check file is PDF or DOCX
- Check file is not corrupted
- Check file is not too large

**Q: Save-confirmed fails**
- Verify resume_hash from parse-preview
- Verify parsed object has required fields
- Check database connectivity

**Q: Student ID not returned**
- Check response `success` flag
- Check for warnings in response
- Check database logs

**Q: Already exists = true**
- This is normal for duplicate resumes
- Same file content = same hash
- User can still save or skip

---

## Documentation

- **Implementation Details:** `TWO_STEP_UPLOAD_IMPLEMENTATION.md`
- **Testing Guide:** `TESTING_GUIDE.md`
- **Implementation Summary:** `IMPLEMENTATION_COMPLETE.md`

---

## Support

For issues or questions:
1. Check logs in terminal
2. Review error message in response
3. Refer to testing guide
4. Check implementation documentation

---

**Status:** ✅ Ready for Testing & Production  
**Last Updated:** [Current Date]
