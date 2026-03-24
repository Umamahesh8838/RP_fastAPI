#!/usr/bin/env python
"""
Test script for the two new resume upload endpoints.
Tests /resume/parse-preview and /resume/save-confirmed
"""
import requests
import json
from io import BytesIO

BASE_URL = "http://127.0.0.1:8080"

# Sample resume text
resume_text = """
JOHN DOE
john.doe@email.com | +1-555-123-4567 | LinkedIn: /in/johndoe | GitHub: github.com/johndoe

PROFESSIONAL SUMMARY
Experienced Full-Stack Developer with 5 years of experience building scalable web applications using Python, JavaScript, and React. Strong background in cloud technologies and DevOps practices.

EDUCATION
Bachelor of Technology in Computer Science
University of Technology | 2018 - 2022
GPA: 3.8/4.0 | Specialization: Web Development

EXPERIENCE
Senior Developer | TechCorp Solutions | Jan 2021 - Present
- Developed RESTful APIs using FastAPI and Python
- Implemented microservices architecture for distributed systems
- Led a team of 3 developers in agile environment
- Tech Stack: Python, FastAPI, PostgreSQL, Docker, Kubernetes

Junior Developer | StartupXYZ | Jun 2020 - Dec 2020
- Built responsive web applications using React and JavaScript
- Collaborated with UX team to implement UI/UX improvements
- Tech Stack: React, JavaScript, Node.js, MongoDB

SKILLS
Languages: Python, JavaScript, Java, SQL
Frameworks: FastAPI, Django, React, Express.js
Databases: PostgreSQL, MongoDB, MySQL
Tools: Docker, Kubernetes, Git, AWS

CERTIFICATIONS
- AWS Certified Solutions Architect - Associate (2021)
- Python Professional Certification (2020)

INTERESTS
Open Source Contribution | Machine Learning | Cloud Computing
"""

def create_test_pdf():
    """Create a minimal PDF with resume text for testing."""
    text = resume_text
    pdf_header = b'%PDF-1.4\n'
    pdf_obj1 = b'1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n'
    pdf_obj2 = b'2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n'
    pdf_obj3 = b'3 0 obj<</Type/Page/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>/MediaBox[0 0 612 792]/Contents 5 0 R>>endobj\n'
    pdf_obj4 = b'4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n'
    text_bytes = text.encode()
    stream_length = len(text_bytes)
    pdf_obj5 = f'5 0 obj<</Length {stream_length}>>stream\n'.encode() + text_bytes + b'\nendstream\nendobj\n'
    pdf_xref = b'xref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000214 00000 n\n0000000281 00000 n\ntrailer<</Size 6/Root 1 0 R>>\nstartxref\n374\n%%EOF'
    
    return pdf_header + pdf_obj1 + pdf_obj2 + pdf_obj3 + pdf_obj4 + pdf_obj5 + pdf_xref

def test_parse_preview():
    """Test the /resume/parse-preview endpoint."""
    print("\n" + "="*80)
    print("TEST 1: /resume/parse-preview (No Database Save)")
    print("="*80)
    
    url = f"{BASE_URL}/resume/parse-preview"
    pdf_bytes = create_test_pdf()
    
    files = {'file': ('test_resume.pdf', BytesIO(pdf_bytes))}
    
    try:
        r = requests.post(url, files=files, timeout=60)
        data = r.json()
        
        print(f"\nStatus Code: {r.status_code}")
        
        if r.status_code == 200:
            print("✅ SUCCESS - Parse Preview endpoint working!")
            print(f"\nResponse Structure:")
            print(f"  - success: {data.get('success')}")
            
            parsed_data = data.get('data', {})
            print(f"  - resume_hash: {parsed_data.get('resume_hash', 'N/A')[:16]}...")
            print(f"  - already_exists: {parsed_data.get('already_exists')}")
            
            if 'parsed' in parsed_data:
                parsed = parsed_data['parsed']
                print(f"\n  Parsed Resume Data:")
                print(f"    - First Name: {parsed.get('first_name')}")
                print(f"    - Last Name: {parsed.get('last_name')}")
                print(f"    - Email: {parsed.get('email')}")
                print(f"    - Contact: {parsed.get('contact_number')}")
                print(f"    - GitHub: {parsed.get('github_url')}")
                print(f"    - Education Count: {len(parsed.get('education', []))}")
                print(f"    - Experience Count: {len(parsed.get('workexp', []))}")
                print(f"    - Skills Count: {len(parsed.get('skills', []))}")
                
                # Store for test 2
                return parsed_data.get('resume_hash'), parsed
        else:
            print(f"❌ FAILED - Status {r.status_code}")
            print(f"Error: {data.get('error')}")
            print(f"Detail: {data.get('detail')}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    return None, None

def test_save_confirmed(resume_hash, parsed_data):
    """Test the /resume/save-confirmed endpoint."""
    if not resume_hash or not parsed_data:
        print("\n⚠️  Skipping /resume/save-confirmed test (no preview data)")
        return
    
    print("\n" + "="*80)
    print("TEST 2: /resume/save-confirmed (Save to Database)")
    print("="*80)
    
    url = f"{BASE_URL}/resume/save-confirmed"
    
    payload = {
        "resume_hash": resume_hash,
        "parsed": parsed_data
    }
    
    try:
        r = requests.post(url, json=payload, timeout=60)
        data = r.json()
        
        print(f"\nStatus Code: {r.status_code}")
        
        if r.status_code == 200:
            print("✅ SUCCESS - Save Confirmed endpoint working!")
            print(f"\nResponse Data:")
            
            result_data = data.get('data', {})
            print(f"  - success: {data.get('success')}")
            print(f"  - student_id: {result_data.get('student_id')}")
            print(f"  - resume_hash: {result_data.get('resume_hash', 'N/A')[:16]}...")
            print(f"  - already_existed: {result_data.get('already_existed')}")
            
            summary = result_data.get('summary', {})
            print(f"\n  Save Summary:")
            print(f"    - schools_saved: {summary.get('schools_saved', 0)}")
            print(f"    - educations_saved: {summary.get('educations_saved', 0)}")
            print(f"    - workexps_saved: {summary.get('workexps_saved', 0)}")
            print(f"    - projects_saved: {summary.get('projects_saved', 0)}")
            print(f"    - skills_saved: {summary.get('skills_saved', 0)}")
            print(f"    - languages_saved: {summary.get('languages_saved', 0)}")
            print(f"    - certifications_saved: {summary.get('certifications_saved', 0)}")
            print(f"    - interests_saved: {summary.get('interests_saved', 0)}")
            print(f"    - addresses_saved: {summary.get('addresses_saved', 0)}")
            
            warnings = result_data.get('warnings', [])
            if warnings:
                print(f"\n  Warnings ({len(warnings)}):")
                for w in warnings[:3]:
                    print(f"    - {w}")
        else:
            print(f"❌ FAILED - Status {r.status_code}")
            print(f"Error: {data.get('error')}")
            print(f"Detail: {data.get('detail')}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    print("\n🔍 Testing New Resume Upload Endpoints\n")
    
    # Test 1: Parse Preview
    resume_hash, parsed_data = test_parse_preview()
    
    # Test 2: Save Confirmed
    test_save_confirmed(resume_hash, parsed_data)
    
    print("\n" + "="*80)
    print("✅ All tests completed!")
    print("="*80 + "\n")
