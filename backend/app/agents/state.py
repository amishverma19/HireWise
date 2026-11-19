from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

from app.schemas import (
    BulletImprovement,
    HireWiseAnalysisResult,
    JobDescription,
    MatchResult,
    ParsedResume,
)


class HireWiseState(TypedDict, total=False):
    """
    Shared State across all LangGraph agent nodes.
    Maintains candidate profile, embeddings, ATS scoring metrics, and rewrites.
    """
    resume_id: str
    user_id: Optional[str]
    pdf_bytes: Optional[bytes]
    raw_text: str
    job_id: Optional[str]
    job_description: JobDescription
    parsed_resume: Optional[ParsedResume]
    chunks: List[str]
    retrieval_stats: Dict[str, Any]
    match_result: Optional[MatchResult]
    ats_score: float
    bullet_improvements: List[BulletImprovement]
    interview_tips: List[str]
    agent_logs: List[str]
    file_hash: str
    final_result: Optional[HireWiseAnalysisResult]

