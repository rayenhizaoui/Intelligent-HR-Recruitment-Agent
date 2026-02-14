"""
Skill Extraction Tools

This module contains tools for extracting skills, generating summaries,
and normalizing experience data from CV text.
"""

from typing import Optional, List
from langchain_core.tools import tool
import re
from datetime import datetime

# JSON Schema for structured skill extraction output
SKILL_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "skills": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of technical and soft skills"
        },
        "experience_years": {
            "type": "integer",
            "description": "Total years of professional experience"
        },
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "degree": {"type": "string"},
                    "field": {"type": "string"},
                    "institution": {"type": "string"},
                    "year": {"type": "integer"}
                }
            }
        },
        "certifications": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Professional certifications"
        },
        "projects_count": {
            "type": "integer",
            "description": "Number of projects identified"
        }
    },
    "required": ["skills", "experience_years", "education", "certifications"]
}


@tool
def skill_extractor_tool(cv_text: str) -> dict:
    """
    Extract structured data from CV text using simple keyword matching (fallback)
    or LLM if configured.
    """
    cv_text_lower = cv_text.lower()
    
    # Enhanced tech keywords mapping
    # Map keywords to categories for better organization (internal helper)
    skill_categories = {
        "AI/ML": ["machine learning", "deep learning", "ai", "nlp", "computer vision", 
                  "pytorch", "tensorflow", "keras", "scikit-learn", "pandas", "numpy", 
                  "rag", "langchain", "transformers", "llms", "prompt engineering", "agents"],
        "Web/Fullstack": ["html", "css", "javascript", "typescript", "react", "angular", "vue",
                          "node.js", "express", "flask", "django", "fastapi", "spring boot", ".net", "next.js"],
        "Cloud/DevOps": ["aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "git", 
                         "mlflow", "grafana", "linux"],
        "Languages": ["python", "java", "c++", "sql", "nosql", "r", "dax"],
        "Soft Skills": ["communication", "leadership", "project management", "agile", "scrum"]
    }
    
    found_skills = []
    
    # Flatten the list for searching
    all_keywords = []
    for cat, keywords in skill_categories.items():
        all_keywords.extend(keywords)
    
    for skill in all_keywords:
        if skill in cv_text_lower:
            found_skills.append(skill.title())

    # Deduplicate
    found_skills = list(set(found_skills))
    
    # Advanced Experience Extraction Logic
    years = 0
    # 1. Look for explicit "X years experience"
    match = re.search(r'(\d+)\+?\s*years?', cv_text_lower)
    if match:
        years = int(match.group(1))
    
    # 2. Heuristic: Look for date ranges in CV text
    # e.g. "July 2025 August 2025" or "2020 - 2023"
    # This is rough estimation
    date_matches = re.findall(r'\b(20\d{2})\b', cv_text)
    if not years and len(date_matches) >= 2:
        dates = [int(y) for y in date_matches]
        min_year = min(dates)
        max_year = max(dates)
        diff = max_year - min_year
        if diff > 0 and diff < 40: # Reasonable career span
            years = diff
            
    # Heuristic for students/interns if years is still 0 but we see "Intern"
    is_intern = "intern" in cv_text_lower
    if years == 0 and is_intern:
        # Check if multiple internships (dates) imply some experience
        # Let's count occurrences of "Intern"
        intern_count = cv_text_lower.count("intern")
        if intern_count > 0:
            # Assume ~3-6 months per internship usually, but let's just say < 1 year
             pass # keep 0 but mark context later?
    
    
    # Improved Education Extraction
    education = []
    # Look for common degrees with better context
    if "bachelor" in cv_text_lower or "baccalaureate" in cv_text_lower or "licence" in cv_text_lower:
        # Try to find field
        field = "Computer Science/Engineering" # Default inference
        if "data science" in cv_text_lower:
            field = "Data Science"
        elif "mathematics" in cv_text_lower:
            field = "Mathematics"
            
        education.append({
            "degree": "Bachelor's/Baccalaureate", 
            "field": field, 
            "institution": "University/College (Inferred)"
        })
        
    if "engineer" in cv_text_lower or "engineering program" in cv_text_lower:
         education.append({
            "degree": "Engineering Degree", 
            "field": "Data Science/AI" if "data science" in cv_text_lower else "Engineering", 
            "institution": "ESPRIT (Inferred)" if "esprit" in cv_text_lower else "Engineering School"
        })

    if "master" in cv_text_lower:
        education.append({
             "degree": "Master's Degree", 
             "field": "Relevant Field", 
             "institution": "University (Inferred)"
        })

    # Deduplicate education entries slightly
    # (Skip complex logic for now, just keep unique degree names)
    unique_edu = []
    seen_degrees = set()
    for edu in education:
        if edu["degree"] not in seen_degrees:
            unique_edu.append(edu)
            seen_degrees.add(edu["degree"])
    
    # Extract Project Count
    project_count = cv_text_lower.count("project") 

    return {
        "skills": found_skills if found_skills else ["No specific skills detected"],
        "experience_years": years,
        "education": unique_edu,
        "certifications": [],
        "projects_count": project_count,
        "note": "Extracted using enhanced keyword matching."
    }


def extract_skills(text: str) -> dict:
    """Core skill extraction function (non-tool version)."""
    return skill_extractor_tool.invoke(text)


@tool
def candidate_summarizer(input_data: dict) -> str:
    """
    Generate a more professional executive summary.
    
    Args:
        input_data: Dict containing 'cv_text' and optionally 'extracted_skills'.
    """
    cv_text = input_data.get("cv_text", "")
    extracted_skills = input_data.get("extracted_skills", None)

    if not cv_text or len(cv_text.strip()) < 30:
        return "Insufficient information available to generate a candidate summary."

    skills = extracted_skills.get("skills", []) if extracted_skills else []
    experience_years = extracted_skills.get("experience_years", 0) if extracted_skills else 0
    education = extracted_skills.get("education", []) if extracted_skills else []
    project_count = extracted_skills.get("projects_count", 0) if extracted_skills else 0

    # Determine seniority/level
    level = "Entry-Level"
    if experience_years >= 5:
        level = "Senior"
    elif experience_years >= 2:
        level = "Mid-Level"
    elif "intern" in cv_text.lower():
        level = "Internship/Junior"

    # Top skills (prioritize hard skills)
    top_skills = sorted(skills[:8], key=len, reverse=True) # heuristics for display
    skills_str = ", ".join(top_skills)

    education_str = "an academic background"
    if education:
        deg = education[0]['degree']
        field = education[0]['field']
        education_str = f"a {deg} in {field}"

    summary = (
        f"**Candidate Profile:** {level} professional with {experience_years}+ years of experience and {education_str}. "
        f"Demonstrates strong capability in **{skills_str}**, supported by a portfolio of approximately {project_count} projects. "
        f"The candidate appears well-suited for roles requiring expertise in specific technologies listed above."
    )

    return summary


def _parse_year(value: str) -> Optional[int]:
    match = re.search(r"\b(19|20)\d{2}\b", value)
    return int(match.group()) if match else None


def _parse_month_year(value: str) -> Optional[datetime]:
    try:
        if not value: return None
        return datetime.strptime(value.strip(), "%b %Y")
    except ValueError:
        try:
            return datetime.strptime(value.strip(), "%B %Y")
        except ValueError:
            return None


def experience_normalizer(date_string: str) -> int:
    """
    Convert varied date formats to total years of experience.
    """
    if not date_string:
        return 0

    text = date_string.lower().strip()
    now = datetime.now()

    match_years = re.search(r"(\d+)\s+years?", text)
    if match_years:
        return int(match_years.group(1))

    if "present" in text or "current" in text:
        parts = re.split(r"-|to", text)
        if parts:
            start = _parse_month_year(parts[0].title()) 
            if not start:
                y = _parse_year(parts[0])
                if y: start = datetime(y, 1, 1)
            
            if start:
                return max(0, now.year - start.year)

    years = re.findall(r"\b(19|20)\d{2}\b", text)
    if len(years) >= 2:
        return abs(int(years[1]) - int(years[0]))

    parts = re.split(r"-|to", text)
    if len(parts) == 2:
        start = _parse_month_year(parts[0].title())
        end = _parse_month_year(parts[1].title())
        if start and end:
            return max(0, end.year - start.year)

    year = _parse_year(text)
    if year:
        return max(0, now.year - year)

    return 0


def aggregate_experience(date_ranges: List[str]) -> int:
    """Calculate total experience from a list of date ranges."""
    total = 0
    if not date_ranges: return 0
    for date_range in date_ranges:
        total += experience_normalizer(date_range)
    return total
