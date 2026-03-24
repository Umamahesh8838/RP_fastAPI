#!/usr/bin/env python
"""
Test both new endpoints with longer timeout for LLM processing
"""
import requests
import time

BASE_URL = 'http://127.0.0.1:8080'
TIMEOUT = 300  # 5 minutes - LLM processing can be slow

print('\nTesting with 5-minute timeout for LLM processing...\n')

# TEST 1: Parse Preview
print('='*70)
print('TEST 1: POST /resume/parse-preview')
print('='*70)

parse_url = f'{BASE_URL}/resume/parse-preview'
with open('test_resume.docx', 'rb') as f:
    files = {'file': f}
    print('Sending request (this may take a minute or two)...')
    start = time.time()
    try:
        r = requests.post(parse_url, files=files, timeout=TIMEOUT)
        elapsed = time.time() - start
        data = r.json()
        
        print(f'Response received in {elapsed:.1f}s')
        print(f'Status Code: {r.status_code}\n')
        
        if r.status_code == 200:
            print('✅ SUCCESS!\n')
            result = data.get('data', {})
            
            print('Response Data:')
            print(f'  - resume_hash: {result.get("resume_hash", "")[0:24]}...')
            print(f'  - already_exists: {result.get("already_exists")}')
            
            if 'parsed' in result:
                parsed = result['parsed']
                print(f'\nParsed Resume:')
                print(f'  - first_name: {parsed.get("first_name")}')
                print(f'  - last_name: {parsed.get("last_name")}')
                print(f'  - email: {parsed.get("email")}')
                print(f'  - contact_number: {parsed.get("contact_number")}')
                print(f'  - education count: {len(parsed.get("education", []))}')
                print(f'  - workexp count: {len(parsed.get("workexp", []))}')
                print(f'  - skills count: {len(parsed.get("skills", []))}')
                
                # Store for next test
                resume_hash = result.get('resume_hash')
                parsed_obj = result.get('parsed')
                
                # TEST 2: Save Confirmed
                print('\n' + '='*70)
                print('TEST 2: POST /resume/save-confirmed')
                print('='*70 + '\n')
                
                save_url = f'{BASE_URL}/resume/save-confirmed'
                payload = {'resume_hash': resume_hash, 'parsed': parsed_obj}
                
                print('Sending save request...')
                start2 = time.time()
                r2 = requests.post(save_url, json=payload, timeout=TIMEOUT)
                elapsed2 = time.time() - start2
                data2 = r2.json()
                
                print(f'Response received in {elapsed2:.1f}s')
                print(f'Status Code: {r2.status_code}\n')
                
                if r2.status_code == 200:
                    print('✅ SUCCESS!\n')
                    result2 = data2.get('data', {})
                    
                    print('Response Data:')
                    print(f'  - student_id: {result2.get("student_id")}')
                    print(f'  - resume_hash: {result2.get("resume_hash", "")[0:24]}...')
                    print(f'  - already_existed: {result2.get("already_existed")}')
                    
                    summary = result2.get('summary', {})
                    print(f'\nSaved Items:')
                    for key, count in summary.items():
                        if count > 0:
                            print(f'  - {key}: {count}')
                    
                    warnings = result2.get('warnings', [])
                    if warnings:
                        print(f'\nWarnings ({len(warnings)}):')
                        for w in warnings[:3]:
                            print(f'  - {w}')
                else:
                    print(f'❌ FAILED\n')
                    print(f'Error: {data2.get("error")}')
                    if data2.get("detail"):
                        print(f'Detail: {data2.get("detail")}')
        else:
            print(f'❌ FAILED\n')
            print(f'Error: {data.get("error")}')
            if data.get("detail"):
                print(f'Detail: {data.get("detail")}')
                
    except requests.exceptions.Timeout:
        print(f'❌ TIMEOUT after {TIMEOUT}s')
        print('The LLM processing took too long. Try with a real resume or check Ollama.')
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')

print('\n' + '='*70)
print('Test Complete')
print('='*70 + '\n')
