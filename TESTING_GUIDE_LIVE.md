# 🚀 Testing the New Endpoints - Live Guide

## ✅ Server Status
- **Status**: RUNNING ✅
- **Port**: 127.0.0.1:8080
- **Process ID**: 8824
- **Swagger UI**: http://127.0.0.1:8080/docs

---

## 🧪 How to Test Right Now

### Option 1: Swagger UI (Easiest - Recommended) ⭐

**Step 1:** Open your browser
```
http://127.0.0.1:8080/docs
```

**Step 2:** Find the "resume" section and expand it

You should see 3 endpoints:
```
POST /resume/upload           (Original - still works)
POST /resume/parse-preview    (NEW - Testing this!)
POST /resume/save-confirmed   (NEW - For after preview)
```

**Step 3:** Click on `/resume/parse-preview`

**Step 4:** Click "Try it out" button

**Step 5:** Click "Choose File" and select your PDF resume
```
Resume_lokareddy[1].pdf  (or any PDF resume)
```

**Step 6:** Click "Execute" button

**Step 7:** Wait for response (30-60 seconds for LLM processing)

**Expected Success Response (200):**
```json
{
  "success": true,
  "data": {
    "resume_hash": "a1b2c3d4e5f6...",
    "already_exists": false,
    "parsed": {
      "first_name": "Lokareddy",
      "last_name": "...",
      "email": "...",
      "education": [...],
      "workexp": [...],
      ...
    }
  }
}
```

**Step 8:** Copy the `resume_hash` and `parsed` object from response

**Step 9:** Click on `/resume/save-confirmed`

**Step 10:** Click "Try it out" button

**Step 11:** In the Request body, paste:
```json
{
  "resume_hash": "paste_hash_here",
  "parsed": {paste_parsed_object_here}
}
```

**Step 12:** Click "Execute"

**Expected Success Response (200):**
```json
{
  "success": true,
  "data": {
    "student_id": 42,
    "resume_hash": "a1b2c3d4e5f6...",
    "already_existed": false,
    "summary": {
      "schools_saved": 1,
      "educations_saved": 1,
      "workexps_saved": 2,
      "skills_saved": 5,
      ...
    },
    "warnings": []
  }
}
```

---

### Option 2: curl Command (Advanced)

**Test parse-preview:**
```bash
curl -X POST http://127.0.0.1:8080/resume/parse-preview \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@Resume_lokareddy[1].pdf;type=application/pdf"
```

**Then use the response hash to test save-confirmed:**
```bash
curl -X POST http://127.0.0.1:8080/resume/save-confirmed \
  -H "Content-Type: application/json" \
  -d '{
    "resume_hash": "PASTE_HASH_HERE",
    "parsed": {PASTE_PARSED_OBJECT_HERE}
  }'
```

---

### Option 3: Python Script

```python
import requests

url = 'http://127.0.0.1:8080/resume/parse-preview'
with open('Resume_lokareddy[1].pdf', 'rb') as f:
    files = {'file': f}
    r = requests.post(url, files=files, timeout=120)

if r.status_code == 200:
    data = r.json()
    print("✅ Parse Preview SUCCESS!")
    print(f"Student: {data['data']['parsed']['first_name']}")
else:
    print(f"❌ Error: {r.json()}")
```

---

## ✨ Expected Behavior

### Parse Preview Endpoint
- ✅ Accepts PDF or DOCX files
- ✅ Extracts text automatically
- ✅ Checks for duplicate resume (by hash)
- ✅ Parses with LLM (2-pass system)
- ✅ Returns parsed data **WITHOUT saving to database**
- ✅ Returns resume_hash for later confirmation
- ⏱️ Takes 30-60 seconds (LLM processing)

### Save Confirmed Endpoint
- ✅ Accepts JSON with hash + parsed resume
- ✅ Validates the data
- ✅ Saves everything to database
- ✅ Returns student_id (the database record ID)
- ✅ Returns summary of what was saved
- ✅ Collects warnings for non-critical issues
- ⏱️ Takes 5-10 seconds (database writes)

---

## 🔍 Verification Checklist

After testing, verify:

- [ ] Parse preview returns data without "Undocumented" error
- [ ] Parse preview returns `resume_hash` 
- [ ] Parse preview returns `already_exists: false` for new resume
- [ ] Parse preview returns `parsed` object with personal data
- [ ] Save confirmed accepts the hash and parsed object
- [ ] Save confirmed returns `student_id` (a number)
- [ ] Save confirmed returns `summary` with counts
- [ ] No errors in the response

---

## 📊 What You Should See

### Parse Preview Response Structure
```
✅ success: true
✅ data:
   ├─ resume_hash: "abc123..." (long string)
   ├─ already_exists: false (boolean)
   └─ parsed:
      ├─ first_name: "John"
      ├─ last_name: "Doe"
      ├─ email: "john@..."
      ├─ education: [...]
      ├─ workexp: [...]
      ├─ skills: [...]
      └─ ... (more fields)
```

### Save Confirmed Response Structure
```
✅ success: true
✅ data:
   ├─ student_id: 42 (a number)
   ├─ resume_hash: "abc123..."
   ├─ already_existed: false
   ├─ summary:
   │  ├─ schools_saved: 0
   │  ├─ educations_saved: 1
   │  ├─ workexps_saved: 2
   │  ├─ projects_saved: 0
   │  ├─ skills_saved: 5
   │  ├─ languages_saved: 1
   │  ├─ certifications_saved: 1
   │  ├─ interests_saved: 2
   │  └─ addresses_saved: 0
   └─ warnings: [] (empty if no issues)
```

---

## ⏱️ Timing Expectations

**Parse Preview:**
- File upload: 1-2 seconds
- Text extraction: 2-5 seconds
- Duplicate check: 1 second
- LLM parsing (2 passes): 20-50 seconds
- **Total: 30-60 seconds** ⏳

**Save Confirmed:**
- Validation: <1 second
- Database saves: 3-8 seconds
- **Total: 5-10 seconds** ⏳

---

## 🐛 Troubleshooting

### Issue: "Failed to fetch" or connection error
**Solution:** 
- Server may have crashed. Check if process 8824 still exists:
  ```bash
  netstat -ano | findstr :8080
  ```
- If not, restart: `uvicorn main:app --port 8080`

### Issue: Timeout (waiting >60 seconds)
**Solution:**
- LLM (Ollama) might be busy
- Check Ollama is running: `curl http://localhost:11434/api/tags`
- Try again in a moment

### Issue: "Unsupported file type"
**Solution:**
- Only PDF and DOCX supported
- Ensure file extension is .pdf or .docx

### Issue: "File too large"
**Solution:**
- Max size is typically 50MB
- Try smaller resume file

### Issue: "Resume already processed"
**Solution:**
- This is expected if you test with same file twice
- Use different resume file to test again
- Or wait - hash stored in database prevents duplicates

### Issue: Response shows "parsed" but got JSON error
**Solution:**
- Old server code may be cached
- Restart server:
  ```bash
  taskkill /IM python.exe /F
  Start-Sleep 2
  uvicorn main:app --port 8080
  ```

---

## 📈 Success Indicators

✅ All these should be true:
- [ ] Endpoints appear in Swagger UI at /docs
- [ ] Parse preview endpoint accepts file upload
- [ ] Response comes back without error
- [ ] Resume_hash is present in response
- [ ] Parsed data has first_name, email, etc.
- [ ] Save confirmed accepts the hash
- [ ] Save confirmed returns student_id
- [ ] Student record appears in database

---

## 🎯 Full Testing Flow

```
1. Open: http://127.0.0.1:8080/docs
         ↓
2. Find: /resume/parse-preview
         ↓
3. Click: "Try it out"
         ↓
4. Upload: Resume_lokareddy[1].pdf
         ↓
5. Wait: 30-60 seconds
         ↓
6. Get: resume_hash + parsed data
         ↓
7. Copy: Both values
         ↓
8. Find: /resume/save-confirmed
         ↓
9. Click: "Try it out"
         ↓
10. Paste: Hash + parsed object
         ↓
11. Execute: Request
         ↓
12. Get: student_id + summary
         ↓
✅ SUCCESS!
```

---

## 📞 Questions?

**Q: How long does parsing take?**
A: 30-60 seconds (Ollama LLM processing time)

**Q: Will it break existing /resume/upload?**
A: No! Old endpoint still works. Use whichever you prefer.

**Q: Can I edit data before saving?**
A: Yes! Frontend gets parsed data from step 1, can edit, then send to step 2.

**Q: What if preview shows wrong data?**
A: Don't confirm! Cancel without saving. Fix resume file and try again.

**Q: Where does it save data?**
A: MySQL database (campus5), tables: tbl_cp_student, tbl_cp_education, etc.

**Q: Can I test twice with same file?**
A: Yes, but second time will show "already_exists: true"

---

## 🎊 You're All Set!

Server is running, endpoints are ready, documentation is complete.

**Next Step:** 
1. Open http://127.0.0.1:8080/docs
2. Test /resume/parse-preview with your resume
3. Then test /resume/save-confirmed
4. Verify database has your record

Good luck! 🚀
