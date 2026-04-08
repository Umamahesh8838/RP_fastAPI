import asyncio
from database import engine
from sqlalchemy import text

async def list_all_tables():
    """List all tables currently in Azure SQL database"""
    query = """
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_TYPE='BASE TABLE' 
    ORDER BY TABLE_NAME
    """
    
    async with engine.connect() as conn:
        result = await conn.execute(text(query))
        tables = result.fetchall()
    
    print(f"\n{'='*60}")
    print(f"TABLES IN AZURE SQL DATABASE: campus5")
    print(f"{'='*60}\n")
    
    for i, (table_name,) in enumerate(tables, 1):
        print(f"{i:2d}. {table_name}")
    
    print(f"\n{'='*60}")
    print(f"TOTAL TABLES: {len(tables)}")
    print(f"{'='*60}\n")
    
    # List of tables that SHOULD exist
    required_tables = [
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
        'tbl_cp_m2m_session_question_response',
        'tbl_cp_resume_hashes'  # This was auto-created
    ]
    
    existing_table_names = [t[0] for t in tables]
    
    print("\nMISSING TABLES:")
    print(f"{'='*60}")
    missing = []
    for table in required_tables:
        if table not in existing_table_names:
            missing.append(table)
            print(f"  ✗ {table}")
    
    if not missing:
        print("  ✓ ALL TABLES PRESENT!")
    
    print(f"\n  Total Missing: {len(missing)}/{len(required_tables)}")
    print(f"{'='*60}\n")
    
    return len(tables), len(missing)

if __name__ == "__main__":
    try:
        total, missing = asyncio.run(list_all_tables())
    except Exception as e:
        print(f"\nERROR: {e}")
        print(f"Make sure database.py is configured correctly")
