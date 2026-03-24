#!/usr/bin/env python
"""Test the new endpoints with DOCX file"""
import requests
import json

BASE_URL = 'http://127.0.0.1:8080'

print('\n' + '='*80)
print('TEST 1: /resume/parse-preview with DOCX file')
print('='*80 + '\n')

url = f'{BASE_URL}/resume/parse-preview'
with open('test_resume.docx', 'rb') as f:
    files = {'file': f}
    r = requests.post(url, files=files, timeout=60)

data = r.json()
print(f'Status Code: {r.status_code}')

if r.status_code == 200:
    print('✅ SUCCESS!')
    print(f'  Success: {data.get("success")}')
    result = data.get('data', {})
    print(f'  Resume Hash: {result.get("resume_hash", "N/A")[:24]}...')
    print(f'  Already Exists: {result.get("already_exists")}')
    
    if 'parsed' in result:
        parsed = result['parsed']
        print(f'\n  Parsed Data:')
        print(f'    First Name: {parsed.get("first_name")}')
        print(f'    Last Name: {parsed.get("last_name")}')
        print(f'    Email: {parsed.get("email")}')
        print(f'    Contact: {parsed.get("contact_number")}')
        print(f'    Education Items: {len(parsed.get("education", []))}')
        print(f'    Experience Items: {len(parsed.get("workexp", []))}')
        print(f'    Skills: {len(parsed.get("skills", []))} found')
        
        resume_hash = result.get('resume_hash')
        parsed_obj = result.get('parsed')
        
        # Test 2: Save Confirmed
        print('\n' + '='*80)
        print('TEST 2: /resume/save-confirmed with parsed data')
        print('='*80 + '\n')
        
        save_url = f'{BASE_URL}/resume/save-confirmed'
        payload = {'resume_hash': resume_hash, 'parsed': parsed_obj}
        r2 = requests.post(save_url, json=payload, timeout=60)
        data2 = r2.json()
        
        print(f'Status Code: {r2.status_code}')
        if r2.status_code == 200:
            print('✅ SUCCESS!')
            result2 = data2.get('data', {})
            print(f'  Student ID: {result2.get("student_id")}')
            print(f'  Resume Hash Match: {result2.get("resume_hash") == resume_hash}')
            print(f'  Already Existed: {result2.get("already_existed")}')
            summary = result2.get('summary', {})
            print(f'  Summary:')
            for key, val in summary.items():
                if val > 0:
                    print(f'    {key}: {val}')
        else:
            print(f'❌ FAILED')
            print(f'  Error: {data2.get("error")}')
else:
    print(f'❌ FAILED')
    print(f'  Error: {data.get("error")}')
    print(f'  Detail: {data.get("detail")}')

print('\n' + '='*80)
print('✅ All tests completed!')
print('='*80 + '\n')
