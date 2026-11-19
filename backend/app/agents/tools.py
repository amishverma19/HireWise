from datetime import datetime
import re
from typing import Any, Dict, List
from langchain_core.tools import tool


@tool
def calculate_experience_years(experiences: List[Dict[str, Any]]) -> float:
    """
    Deterministically computes total professional experience years from employment history dates.
    Handles date strings like 'Jan 2020', '2021', 'Present', 'current'.
    """
    total_months = 0
    current_year = datetime.now().year
    current_month = datetime.now().month

    def parse_year_month(date_str: str) -> tuple[int, int]:
        clean = date_str.strip().lower()
        if not clean or "present" in clean or "current" in clean or "now" in clean:
            return current_year, current_month

        # Find 4 digit year
        year_match = re.search(r"\b(19\d\d|20\d\d)\b", clean)
        year = int(year_match.group(1)) if year_match else current_year

        month_map = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
        }
        month = 1
        for m_name, m_val in month_map.items():
            if m_name in clean:
                month = m_val
                break
        return year, month

    for exp in experiences:
        if isinstance(exp, dict):
            # If explicit years provided and positive
            explicit_years = exp.get("years")
            if explicit_years and float(explicit_years) > 0:
                total_months += int(float(explicit_years) * 12)
                continue

            start_str = str(exp.get("start_date", ""))
            end_str = str(exp.get("end_date", ""))
            if start_str:
                s_year, s_month = parse_year_month(start_str)
                e_year, e_month = parse_year_month(end_str)
                diff_months = (e_year - s_year) * 12 + (e_month - s_month)
                total_months += max(3, diff_months)  # at least 3 months per listed role

    total_years = round(total_months / 12.0, 1)
    return max(1.0, total_years) if experiences else 0.0


@tool
def calculate_ats_score(
    matched_skills: List[str],
    missing_skills: List[str],
    exp_years_actual: float,
    exp_years_required: float,
    vector_similarity: float
) -> Dict[str, Any]:
    """
    Deterministic mathematical ATS scoring engine:
    - 40% weight on exact keyword/skill overlap percentage
    - 35% weight on semantic vector cosine similarity
    - 25% weight on required experience duration math
    Returns detailed sub-scores and final composite ATS score (0-100).
    """
    total_skills = len(matched_skills) + len(missing_skills)
    skill_score = (len(matched_skills) / total_skills * 100.0) if total_skills > 0 else 70.0
    
    # Vector similarity is in range [0.0, 1.0], scale to 100
    vector_score = min(100.0, max(0.0, vector_similarity * 100.0))

    # Experience score calculation:
    # If candidate meets or exceeds required years: 100
    # Otherwise proportional to required years with a reasonable floor
    if exp_years_required <= 0:
        exp_score = 100.0
    else:
        ratio = exp_years_actual / exp_years_required
        exp_score = min(100.0, ratio * 100.0)

    # Weighted Composite ATS Score
    # 40% Skill Match, 35% Vector Semantics, 25% Experience Math
    composite = (0.40 * skill_score) + (0.35 * vector_score) + (0.25 * exp_score)
    overall_score = round(composite, 1)

    return {
        "overall_score": overall_score,
        "skill_match_score": round(skill_score, 1),
        "vector_similarity_score": round(vector_score, 1),
        "experience_score": round(exp_score, 1),
        "passed_threshold": overall_score >= 80.0
    }

