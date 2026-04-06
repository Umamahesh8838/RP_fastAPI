"""
Resume Quality Score Calculator

Calculates a quality score (0-100) for parsed resumes based on:
- Contact information completeness
- Education details
- Skills count and diversity
- Work experience
- Projects and portfolio
- Certifications
- Languages
- Areas of interest
"""


def calculate_resume_quality(parsed: dict) -> dict:
    """
    Calculates a quality score for a parsed resume.
    
    Scores the resume out of 100 based on completeness
    and strength of different sections. Also returns
    a grade, list of missing things, and suggestions.
    
    Parameters:
        parsed: the parsed resume dict from Gemini
        
    Returns:
        dict with score, grade, breakdown, missing, suggestions
    """
    
    score = 0
    breakdown = {}
    missing = []
    suggestions = []
    
    # ── CONTACT INFO (20 points total) ──────────────
    contact_score = 0
    
    if parsed.get("first_name") and parsed.get("last_name"):
        contact_score += 5
    else:
        missing.append("Full name")
        
    if parsed.get("email"):
        contact_score += 5
    else:
        missing.append("Email address")
        suggestions.append("Add your email address")
        
    if parsed.get("contact_number"):
        contact_score += 5
    else:
        missing.append("Phone number")
        suggestions.append("Add your phone number")
        
    if parsed.get("linkedin_url"):
        contact_score += 3
    else:
        missing.append("LinkedIn URL")
        suggestions.append("Add your LinkedIn profile URL")
        
    if parsed.get("github_url"):
        contact_score += 2
    else:
        missing.append("GitHub URL")
        suggestions.append("Add your GitHub profile URL")
    
    breakdown["contact_info"] = {
        "score": contact_score,
        "max": 20,
        "label": "Contact Information"
    }
    score += contact_score
    
    # ── EDUCATION (20 points total) ──────────────────
    edu_score = 0
    
    school = parsed.get("school") or []
    education = parsed.get("education") or []
    
    if len(school) >= 1:
        edu_score += 5
        # Check if percentage is filled
        has_pct = any(s.get("percentage") for s in school)
        if has_pct:
            edu_score += 3
        else:
            suggestions.append(
                "Add percentage/marks for school education"
            )
    else:
        missing.append("School education (10th/12th)")
        suggestions.append("Add your 10th and 12th education details")
    
    if len(school) >= 2:
        edu_score += 2
        
    if len(education) >= 1:
        edu_score += 5
        college = education[0]
        if college.get("cgpa") or college.get("percentage"):
            edu_score += 3
        else:
            suggestions.append(
                "Add CGPA or percentage for college education"
            )
        if college.get("specialization_name"):
            edu_score += 2
    else:
        missing.append("College/University education")
        suggestions.append("Add your college degree details")
    
    breakdown["education"] = {
        "score": edu_score,
        "max": 20,
        "label": "Education"
    }
    score += edu_score
    
    # ── SKILLS (15 points total) ──────────────────────
    skills_score = 0
    skills = parsed.get("skills") or []
    skill_count = len(skills)
    
    if skill_count == 0:
        missing.append("Skills")
        suggestions.append("Add your technical skills")
    elif skill_count < 3:
        skills_score += 3
        suggestions.append(
            f"Add more skills — you have {skill_count}, aim for at least 5"
        )
    elif skill_count < 5:
        skills_score += 7
        suggestions.append(
            "Add a few more skills to strengthen your profile"
        )
    elif skill_count < 8:
        skills_score += 10
    else:
        skills_score += 15
    
    breakdown["skills"] = {
        "score": skills_score,
        "max": 15,
        "label": "Skills",
        "count": skill_count
    }
    score += skills_score
    
    # ── WORK EXPERIENCE (20 points total) ────────────
    workexp_score = 0
    workexp = parsed.get("workexp") or []
    workexp_count = len(workexp)
    
    if workexp_count == 0:
        missing.append("Work experience or internships")
        suggestions.append(
            "Add any internships, part-time work, or freelance experience"
        )
    elif workexp_count == 1:
        workexp_score += 12
        exp = workexp[0]
        if exp.get("designation"):
            workexp_score += 3
        if exp.get("employment_type"):
            workexp_score += 2
        if exp.get("start_date") and exp.get("start_date") != "1900-01-01":
            workexp_score += 3
    else:
        workexp_score += 20
    
    breakdown["work_experience"] = {
        "score": workexp_score,
        "max": 20,
        "label": "Work Experience",
        "count": workexp_count
    }
    score += workexp_score
    
    # ── PROJECTS (15 points total) ────────────────────
    projects_score = 0
    projects = parsed.get("projects") or []
    project_count = len(projects)
    
    if project_count == 0:
        missing.append("Projects")
        suggestions.append(
            "Add personal or academic projects to showcase your work"
        )
    elif project_count == 1:
        projects_score += 8
        proj = projects[0]
        if proj.get("project_description"):
            projects_score += 4
        if proj.get("skills_used") and len(proj["skills_used"]) > 0:
            projects_score += 3
    elif project_count == 2:
        projects_score += 12
        has_desc = all(p.get("project_description") for p in projects)
        if has_desc:
            projects_score += 3
    else:
        projects_score += 15
    
    breakdown["projects"] = {
        "score": projects_score,
        "max": 15,
        "label": "Projects",
        "count": project_count
    }
    score += projects_score
    
    # ── CERTIFICATIONS (5 points total) ──────────────
    cert_score = 0
    certifications = parsed.get("certifications") or []
    
    if len(certifications) == 0:
        suggestions.append(
            "Add certifications to stand out — "
            "even free ones from Coursera or Google count"
        )
    elif len(certifications) == 1:
        cert_score += 3
    else:
        cert_score += 5
    
    breakdown["certifications"] = {
        "score": cert_score,
        "max": 5,
        "label": "Certifications",
        "count": len(certifications)
    }
    score += cert_score
    
    # ── LANGUAGES (3 points total) ────────────────────
    lang_score = 0
    languages = parsed.get("languages") or []
    
    if len(languages) == 0:
        missing.append("Languages known")
        suggestions.append("Add languages you speak or write")
    elif len(languages) == 1:
        lang_score += 2
    else:
        lang_score += 3
    
    breakdown["languages"] = {
        "score": lang_score,
        "max": 3,
        "label": "Languages",
        "count": len(languages)
    }
    score += lang_score
    
    # ── INTERESTS (2 points total) ────────────────────
    interest_score = 0
    interests = parsed.get("interests") or []
    
    if len(interests) > 0:
        interest_score += 2
    else:
        suggestions.append(
            "Add your areas of interest like "
            "Machine Learning or Web Development"
        )
    
    breakdown["interests"] = {
        "score": interest_score,
        "max": 2,
        "label": "Interests",
        "count": len(interests)
    }
    score += interest_score
    
    # ── FINAL SCORE AND GRADE ─────────────────────────
    score = min(score, 100)  # cap at 100
    
    if score >= 90:
        grade = "A+"
        grade_label = "Excellent"
        grade_color = "#16a34a"
    elif score >= 80:
        grade = "A"
        grade_label = "Very Good"
        grade_color = "#22c55e"
    elif score >= 70:
        grade = "B+"
        grade_label = "Good"
        grade_color = "#84cc16"
    elif score >= 60:
        grade = "B"
        grade_label = "Above Average"
        grade_color = "#eab308"
    elif score >= 50:
        grade = "C"
        grade_label = "Average"
        grade_color = "#f97316"
    elif score >= 35:
        grade = "D"
        grade_label = "Needs Improvement"
        grade_color = "#ef4444"
    else:
        grade = "F"
        grade_label = "Incomplete Resume"
        grade_color = "#dc2626"
    
    # Keep only top 5 most important suggestions
    suggestions = suggestions[:5]
    
    print(f"[QUALITY SCORE] Score: {score}/100 ({grade} - {grade_label})")
    print(f"[QUALITY SCORE] Missing sections: {len(missing)}")
    print(f"[QUALITY SCORE] Suggestions: {len(suggestions)}")
    
    return {
        "score": score,
        "max_score": 100,
        "grade": grade,
        "grade_label": grade_label,
        "grade_color": grade_color,
        "breakdown": breakdown,
        "missing_sections": missing,
        "suggestions": suggestions,
        "is_strong": score >= 70
    }
