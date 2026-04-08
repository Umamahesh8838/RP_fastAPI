import pyodbc
import os

# Connection string
server = 'artisetsql.database.windows.net'
database = 'campus5'
username = 'artiset'
password = 'Qwerty@123'
driver = '{ODBC Driver 18 for SQL Server}'

conn_str = f'Driver={driver};Server=tcp:{server},1433;Database={database};Uid={username};Pwd={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'

try:
    conn = pyodbc.connect(conn_str, timeout=30)
    cursor = conn.cursor()
    
    # Get existing tables
    cursor.execute("""
        SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME
    """)
    existing_tables = set([row[0] for row in cursor.fetchall()])
    
    print("Existing tables:", len(existing_tables))
    print(sorted(existing_tables))
    
    # Missing table groups
    missing_tables = {
        # Question Bank (3 tables)
        'tbl_cp_mquestions',
        'tbl_cp_m2m_question_options',
        
        # Company & JD (2 tables)
        'tbl_cp_mcompany',
        'tbl_cp_job_description',
        
        # Address (3 tables)
        'tbl_cp_student_address',
        'tbl_cp_college_address',
        'tbl_cp_company_address',
        
        # Round Configuration (2 tables)
        'tbl_cp_jd_round_config',
        'tbl_cp_m2m_jd_round_module',
        
        # Recruitment (1 table)
        'tbl_cp_recruitment_drive',
        
        # Application (2 tables)
        'tbl_cp_application',
        'tbl_cp_application_status_history',
        
        # Exam Session (2 tables)
        'tbl_cp_exam_session',
        'tbl_cp_m2m_exam_question_response',
        
        # Interview Session (3 tables)
        'tbl_cp_interview_session',
        'tbl_cp_m2m_session_module_score',
        'tbl_cp_m2m_session_question_response',
    }
    
    # Also check other tables
    all_needed = {
        'tbl_cp_msalutation', 'tbl_cp_mlanguages', 'tbl_cp_minterests', 
        'tbl_cp_mcourses', 'tbl_cp_mcolleges', 'tbl_cp_mcertifications',
        'tbl_cp_mskills', 'tbl_cp_mmodule', 'tbl_cp_mdifficulty',
        'tbl_cp_mround_result', 'tbl_cp_mattendance', 'tbl_cp_minterviewer',
        'tbl_cp_mcountries', 'tbl_cp_mstates', 'tbl_cp_mcities', 'tbl_cp_mpincodes',
        'tbl_cp_student', 'tbl_cp_student_school', 'tbl_cp_student_education',
        'tbl_cp_msemester', 'tbl_cp_msubjects', 'tbl_cp_college_sem_subject',
        'tbl_cp_student_subject_marks', 'tbl_cp_student_workexp', 'tbl_cp_studentprojects',
        'tbl_cp_m2m_std_skill', 'tbl_cp_m2m_std_lng', 'tbl_cp_m2m_std_interest',
        'tbl_cp_m2m_student_certification', 'tbl_cp_m2m_studentproject_skill',
        'tbl_cp_mquestions', 'tbl_cp_m2m_question_options',
        'tbl_cp_mcompany', 'tbl_cp_job_description',
        'tbl_cp_student_address', 'tbl_cp_college_address', 'tbl_cp_company_address',
        'tbl_cp_jd_round_config', 'tbl_cp_m2m_jd_round_module',
        'tbl_cp_recruitment_drive',
        'tbl_cp_application', 'tbl_cp_application_status_history',
        'tbl_cp_exam_session', 'tbl_cp_m2m_exam_question_response',
        'tbl_cp_interview_session', 'tbl_cp_m2m_session_module_score',
        'tbl_cp_m2m_session_question_response'
    }
    
    actually_missing = all_needed - existing_tables
    
    print("\n\n=== MISSING TABLES ===")
    print(f"Total missing: {len(actually_missing)}")
    for tbl in sorted(actually_missing):
        print(f"  - {tbl}")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
