from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class ExperienceItem(BaseModel):
    role: str = Field(..., description="Job title / role")
    company: str = Field(..., description="Company or organization name")
    start_date: str = Field("", description="Start date (e.g., Jan 2021)")
    end_date: str = Field("", description="End date (e.g., Present, Dec 2023)")
    bullets: List[str] = Field(default_factory=list, description="Responsibilities and achievement bullet points")
    years: float = Field(0.0, description="Calculated duration in years")


class ParsedResume(BaseModel):
    full_name: str = Field("", description="Candidate's full name")
    email: str = Field("", description="Candidate's email address")
    phone: str = Field("", description="Candidate's contact phone number")
    summary: str = Field("", description="Professional summary or bio")
    skills: List[str] = Field(default_factory=list, description="Extracted technical and soft skills")
    experience: List[ExperienceItem] = Field(default_factory=list, description="Work experience history")
    education: List[str] = Field(default_factory=list, description="Educational qualifications")
    projects: List[str] = Field(default_factory=list, description="Key projects mentioned")
    total_years_experience: float = Field(0.0, description="Total computed years of professional experience")


class JobDescription(BaseModel):
    id: str = Field(..., description="Unique identifier for the job opening")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    department: str = Field("Engineering", description="Department or team")
    description: str = Field(..., description="Full text description of the role")
    requirements: List[str] = Field(default_factory=list, description="Key responsibilities and requirements")
    skills_required: List[str] = Field(default_factory=list, description="Mandatory and preferred skills")
    min_years_experience: float = Field(2.0, description="Minimum years of experience required")


class JobDescriptionInput(BaseModel):
    title: str
    company: str
    department: Optional[str] = "Engineering"
    description: str
    requirements: Optional[List[str]] = None
    skills_required: Optional[List[str]] = None
    min_years_experience: Optional[float] = 2.0


class MatchResult(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Final composite ATS Score (0-100)")
    vector_similarity_score: float = Field(..., ge=0.0, le=100.0, description="Semantic vector cosine similarity score (0-100)")
    skill_match_score: float = Field(..., ge=0.0, le=100.0, description="Keyword / skill overlap percentage (0-100)")
    experience_score: float = Field(..., ge=0.0, le=100.0, description="Experience requirement alignment score (0-100)")
    matched_skills: List[str] = Field(default_factory=list, description="Skills present in both resume and job description")
    missing_skills: List[str] = Field(default_factory=list, description="Critical job skills missing from the resume")
    experience_years_required: float = Field(..., description="Minimum required experience years")
    experience_years_actual: float = Field(..., description="Candidate's actual experience years")
    match_summary: str = Field("", description="Executive summary of the candidate's alignment")


class BulletImprovement(BaseModel):
    original: str = Field(..., description="Original bullet point from resume")
    improved: str = Field(..., description="Senior engineer rewritten bullet point following natural STAR methodology with quantified impact")
    critique: str = Field(..., description="Candid recruiter/hiring manager critique highlighting why the old bullet failed and why the rewrite stands out")
    impact_metric: str = Field("", description="Quantifiable engineering metric or KPI (e.g. -45% p99 latency, 2.8x throughput)")
    interview_script: str = Field("", description="Conversational talking script the candidate can speak out loud in technical/behavioral interviews")


class HireWiseAnalysisResult(BaseModel):
    status: str = Field("success", description="Status of the analysis")
    ats_score: float = Field(..., description="Overall calculated ATS score (0-100)")
    passed_threshold: bool = Field(..., description="True if ATS score is >= 80%")
    parsed_profile: ParsedResume = Field(..., description="Structured resume profile")
    match_result: MatchResult = Field(..., description="Detailed ATS match breakdown")
    bullet_improvements: List[BulletImprovement] = Field(default_factory=list, description="STAR bullet rewrites (populated when score < 80)")
    interview_tips: List[str] = Field(default_factory=list, description="Domain interview questions and coaching tips (populated when score >= 80)")
    agent_logs: List[str] = Field(default_factory=list, description="Execution traces from LangGraph agent nodes")


class HealthCheckResponse(BaseModel):
    status: str
    database_connected: bool
    gemini_configured: bool
    version: str


# --- User Authentication Schemas ---

class UserRegisterInput(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")
    full_name: str = Field("", description="Full name of the user")


class UserLoginInput(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Password")


class ForgotPasswordInput(BaseModel):
    email: EmailStr = Field(..., description="User email address for password recovery")


class VerifyResetCodeInput(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")


class ResetPasswordInput(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")
    new_password: str = Field(..., min_length=6, description="New password")


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    created_at: str


class AuthResponse(BaseModel):
    token: str
    user: UserProfile
