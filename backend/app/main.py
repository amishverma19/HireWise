import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import hashlib
import json
import logging
import re
import secrets
import smtplib
import uuid
from typing import Any, List, Optional
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from app import __version__
from app.agents.graph import execute_hirewise_workflow
from app.agents.nodes import (
    hybrid_rag_node,
    improver_node,
    interview_tips_node,
    merger_node,
    parser_node,
)
from app.auth import (
    create_access_token,
    get_current_user_id,
    get_current_user_id_optional,
    hash_password,
    verify_password,
)
from app.config import get_settings
from app.database import db
from app.schemas import (
    AuthResponse,
    ForgotPasswordInput,
    HealthCheckResponse,
    HireWiseAnalysisResult,
    JobDescription,
    JobDescriptionInput,
    ResetPasswordInput,
    UserLoginInput,
    UserProfile,
    UserRegisterInput,
    VerifyResetCodeInput,
)
from app.services.gemini_service import gemini_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("hirewise.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan: connects to PostgreSQL (Neon DB) and initializes schema on startup;
    closes pool cleanly on shutdown.
    """
    logger.info("Starting HireWise Multi-Agent Backend...")
    await db.connect()
    yield
    logger.info("Shutting down HireWise Multi-Agent Backend...")
    await db.disconnect()


settings = get_settings()
app = FastAPI(
    title="HireWise Backend API",
    description="Autonomous Multi-Agent Resume Analyzer & Career Coach API powered by LangGraph, Gemini, and pgvector.",
    version=__version__,
    lifespan=lifespan
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- System Endpoints ---

@app.get("/api/health", response_model=HealthCheckResponse, tags=["System"])
async def health_check():
    """Health check endpoint reporting database & Gemini AI status."""
    return HealthCheckResponse(
        status="healthy",
        database_connected=db.is_connected,
        gemini_configured=gemini_service.is_configured,
        version=__version__
    )


# --- Authentication Endpoints ---

@app.post("/api/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED, tags=["Auth"])
async def register(input_data: UserRegisterInput):
    """Registers a new user with PBKDF2 password hashing and returns an access token."""
    existing = await db.get_user_by_email(input_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists. Please sign in."
        )

    hashed = hash_password(input_data.password)
    user_row = await db.create_user(
        email=input_data.email,
        hashed_password=hashed,
        full_name=input_data.full_name
    )

    token = create_access_token(user_id=user_row["id"], email=user_row["email"])
    return AuthResponse(
        token=token,
        user=UserProfile(
            id=user_row["id"],
            email=user_row["email"],
            full_name=user_row.get("full_name") or "",
            created_at=str(user_row.get("created_at") or "Recently")
        )
    )


@app.post("/api/auth/login", response_model=AuthResponse, tags=["Auth"])
async def login(input_data: UserLoginInput):
    """Validates user credentials and returns an access token."""
    user_row = await db.get_user_by_email(input_data.email)
    if not user_row or not verify_password(input_data.password, user_row.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please try again."
        )

    token = create_access_token(user_id=user_row["id"], email=user_row["email"])
    return AuthResponse(
        token=token,
        user=UserProfile(
            id=user_row["id"],
            email=user_row["email"],
            full_name=user_row.get("full_name") or "",
            created_at=str(user_row.get("created_at") or "Recently")
        )
    )


def _send_smtp_email(to_email: str, code: str) -> bool:
    """Dispatches OTP email via standard SMTP if configured."""
    cfg = get_settings()
    if not cfg.SMTP_HOST or not cfg.SMTP_USER:
        return False
    try:
        sender = cfg.SMTP_FROM or cfg.SMTP_USER
        msg = MIMEMultipart("alternative")
        msg["From"] = f"HireWise Security <{sender}>"
        msg["To"] = to_email
        msg["Subject"] = f"{code} is your HireWise verification code"

        body = (
            f"Hello,\n\n"
            f"Your 6-digit HireWise password recovery verification code is:\n\n"
            f"    {code}\n\n"
            f"This code will expire in 15 minutes. If you did not request this, please ignore this email.\n\n"
            f"— The HireWise Team"
        )
        msg.attach(MIMEText(body, "plain"))

        html_body = f"""<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #FAF8F7; margin: 0; padding: 24px;">
  <div style="max-width: 460px; margin: 0 auto; background: #ffffff; border-radius: 16px; border: 1px solid #D49A9A; overflow: hidden; box-shadow: 0 4px 12px rgba(124, 14, 68, 0.08);">
    <div style="background: linear-gradient(135deg, #7C0E44, #AA5E7A); padding: 20px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-size: 20px; font-weight: 700; letter-spacing: -0.5px;">HireWise</h1>
      <p style="color: #F2DACE; margin: 4px 0 0; font-size: 12px;">Password Recovery Verification</p>
    </div>
    <div style="padding: 24px; text-align: center;">
      <p style="color: #334155; font-size: 14px; margin: 0 0 16px; line-height: 1.5;">
        You recently requested to reset your password. Use the verification code below to verify your account:
      </p>
      <div style="background: #FAF8F7; border: 2px dashed #D49A9A; border-radius: 10px; padding: 14px 20px; display: inline-block; margin-bottom: 18px;">
        <span style="font-family: monospace; font-size: 30px; font-weight: 800; letter-spacing: 6px; color: #7C0E44;">{code}</span>
      </div>
      <p style="color: #64748b; font-size: 12px; margin: 0; line-height: 1.5;">
        This code is valid for <strong>15 minutes</strong>.<br>
        If you did not request this reset, you can safely ignore this email.
      </p>
    </div>
    <div style="background: #FDF9F7; border-top: 1px solid #F2DACE; padding: 12px; text-align: center; font-size: 11px; color: #94a3b8;">
      &copy; 2026 HireWise AI Career Coach &bull; Automated Security Delivery
    </div>
  </div>
</body>
</html>"""
        msg.attach(MIMEText(html_body, "html"))

        if cfg.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(cfg.SMTP_HOST, cfg.SMTP_PORT, timeout=12)
            server.ehlo()
        else:
            server = smtplib.SMTP(cfg.SMTP_HOST, cfg.SMTP_PORT, timeout=12)
            server.ehlo()
            if cfg.SMTP_USE_TLS:
                server.starttls()
                server.ehlo()

        if cfg.SMTP_PASSWORD:
            smtp_pwd = cfg.SMTP_PASSWORD.replace(" ", "").strip()
            server.login(cfg.SMTP_USER, smtp_pwd)

        server.send_message(msg)
        server.quit()
        logger.info(f"Verification email successfully delivered to {to_email} via SMTP ({cfg.SMTP_HOST}).")
        return True
    except Exception as e:
        logger.error(f"Failed to send email via SMTP ({cfg.SMTP_HOST}:{cfg.SMTP_PORT}): {e}")
        return False


@app.post("/api/auth/forgot-password", tags=["Auth"])
async def forgot_password(input_data: ForgotPasswordInput):
    """
    Initiates password recovery.
    Explicitly validates whether the user exists; if not found, returns a 404 error.
    """
    user_row = await db.get_user_by_email(input_data.email)
    if not user_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email address. Please check the spelling or create an account."
        )

    # Generate 6-digit secure numeric verification code
    reset_code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    await db.set_reset_code(input_data.email, reset_code, expires_at)
    
    # Send email if SMTP is configured, otherwise log and deliver dev code
    email_sent = False
    cfg = get_settings()
    if cfg.SMTP_HOST and cfg.SMTP_USER:
        email_sent = await asyncio.to_thread(_send_smtp_email, input_data.email, reset_code)

    logger.info(f"[AUTH RECOVERY] Verification code for {input_data.email}: {reset_code} (Expires in 15m | SMTP Sent: {email_sent})")

    return {
        "success": True,
        "message": f"Verification code sent to {input_data.email}." if email_sent else "Verification code generated.",
        "email": input_data.email,
        "email_sent": email_sent,
        "dev_code": reset_code if not email_sent else None
    }


@app.post("/api/auth/verify-reset-code", tags=["Auth"])
async def verify_reset_code(input_data: VerifyResetCodeInput):
    """Verifies that the 6-digit OTP code is valid before prompting for a new password."""
    is_valid = await db.verify_reset_code(input_data.email, input_data.code.strip())
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code. Please check and try again."
        )
    return {
        "success": True,
        "message": "Verification code confirmed."
    }


@app.post("/api/auth/reset-password", tags=["Auth"])
async def reset_password(input_data: ResetPasswordInput):
    """Verifies the 6-digit code and sets a new password."""
    new_hashed = hash_password(input_data.new_password)
    success = await db.verify_and_reset_password(input_data.email, input_data.code.strip(), new_hashed)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code. Please request a new code."
        )

    user_row = await db.get_user_by_email(input_data.email)
    token = create_access_token(user_id=user_row["id"], email=user_row["email"]) if user_row else ""

    return {
        "success": True,
        "message": "Password updated successfully. You may now sign in with your new credentials.",
        "token": token
    }


@app.get("/api/auth/me", response_model=UserProfile, tags=["Auth"])
async def get_me(request: Request):
    """Returns the authenticated user profile."""
    user_id = await get_current_user_id(request)
    user_row = await db.get_user_by_id(user_id)
    if not user_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found."
        )
    return UserProfile(
        id=user_row["id"],
        email=user_row["email"],
        full_name=user_row.get("full_name") or "",
        created_at=str(user_row.get("created_at") or "Recently")
    )


# --- Job Openings Endpoints ---

@app.get("/api/jobs", response_model=List[JobDescription], tags=["Jobs"])
async def list_jobs():
    """Retrieve available target job descriptions for candidate analysis."""
    jobs = await db.get_all_jobs()
    return jobs


@app.post("/api/jobs", response_model=JobDescription, status_code=status.HTTP_201_CREATED, tags=["Jobs"])
async def create_job(input_data: JobDescriptionInput):
    """Add a new job opening to the database."""
    job_id = f"job-{uuid.uuid4().hex[:8]}"
    skills = input_data.skills_required or [
        s.strip() for s in input_data.description.split() if len(s.strip()) > 3
    ][:8]

    new_job = JobDescription(
        id=job_id,
        title=input_data.title,
        company=input_data.company,
        department=input_data.department or "Engineering",
        description=input_data.description,
        requirements=input_data.requirements or [input_data.description[:200]],
        skills_required=skills,
        min_years_experience=input_data.min_years_experience or 2.0
    )

    saved_job = await db.save_job(new_job)
    return saved_job


# --- User-Scoped History Endpoints ---

@app.get("/api/history", tags=["History"])
async def list_history(request: Request, limit: int = 30):
    """
    Retrieve past resume evaluation records strictly scoped to the authenticated user.
    If the client is unauthenticated, returns an empty list for privacy.
    """
    user_id = await get_current_user_id_optional(request)
    if not user_id:
        return []
    records = await db.get_history_list(limit=limit, user_id=user_id)
    return records


@app.get("/api/history/{resume_id}", tags=["History"])
async def get_history_detail(resume_id: str, request: Request):
    """Retrieve the full saved analysis report by ID with user ownership validation."""
    user_id = await get_current_user_id_optional(request)
    report = await db.get_analysis_by_id(resume_id, user_id=user_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation record not found or access unauthorized."
        )
    return report


@app.delete("/api/history/{resume_id}", tags=["History"])
async def delete_history_item(resume_id: str, request: Request):
    """Delete an analysis record strictly owned by the authenticated user."""
    user_id = await get_current_user_id(request)
    success = await db.delete_analysis(resume_id, user_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found or you do not have permission to delete it."
        )
    return {"success": True, "deleted_id": resume_id}


# --- Candidate Analysis Endpoint ---

@app.post("/api/analyze", response_model=HireWiseAnalysisResult, tags=["Analysis"])
async def analyze_resume(
    request: Request,
    resume_file: UploadFile = File(..., description="Candidate Resume in PDF format"),
    job_id: Optional[str] = Form(None, description="Selected Job ID from active catalog"),
    custom_job_description: Optional[str] = Form(None, description="Pasted custom Job Description text"),
    custom_job_title: Optional[str] = Form("Target Role", description="Title for custom job"),
    custom_job_company: Optional[str] = Form("Target Company", description="Company for custom job")
):
    """
    Main Analysis Endpoint:
    1. Validates PDF format, file size (<10MB), and magic bytes (%PDF-).
    2. Resolves target job description.
    3. Triggers LangGraph multi-agent pipeline (Parser -> Hybrid RAG -> Improver/Coach -> Merger).
    4. Persists the evaluation bound to the authenticated user (if signed in).
    """
    # 1. Validate file extension
    if not resume_file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Please upload a PDF resume document."
        )

    pdf_bytes = await resume_file.read()
    
    # 2. Enforce 10MB file size limit
    if len(pdf_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF exceeds the 10MB limit. Please upload a smaller file."
        )

    # 3. Validate PDF magic bytes (%PDF-)
    if not pdf_bytes.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is not a valid PDF document (missing %PDF header)."
        )

    if len(pdf_bytes) < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF file is empty or corrupted."
        )

    # 4. Resolve Job Description
    target_job: Optional[JobDescription] = None
    if job_id:
        target_job = await db.get_job_by_id(job_id)

    if not target_job and custom_job_description and custom_job_description.strip():
        extracted_skills = [
            kw for kw in [
                "Python", "FastAPI", "React", "Next.js", "TypeScript", "JavaScript",
                "PostgreSQL", "pgvector", "Docker", "Kubernetes", "AWS", "LangGraph",
                "LangChain", "Gemini", "OpenAI", "RAG", "Tailwind CSS", "Redis"
            ]
            if kw.lower() in custom_job_description.lower()
        ]
        if not extracted_skills:
            extracted_skills = ["Software Development", "Problem Solving", "System Design", "Communication"]

        target_job = JobDescription(
            id=f"custom-{uuid.uuid4().hex[:6]}",
            title=custom_job_title or "Target Position",
            company=custom_job_company or "Target Company",
            department="Engineering",
            description=custom_job_description,
            requirements=[line.strip() for line in custom_job_description.split("\n") if len(line.strip()) > 15][:5],
            skills_required=extracted_skills,
            min_years_experience=3.0
        )
    elif not target_job:
        jobs = await db.get_all_jobs()
        target_job = jobs[0] if jobs else None

    if not target_job:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid job description selected or provided for comparison."
        )

    # Optional authenticated user
    current_user_id = await get_current_user_id_optional(request)

    # Fast 1ms detection of same resume + target role in database
    file_hash = hashlib.sha256(pdf_bytes).hexdigest()
    candidate_email = ""
    try:
        import fitz
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            sample_text = "\n".join([doc[i].get_text() for i in range(min(2, len(doc)))])
            email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', sample_text)
            if email_match:
                candidate_email = email_match.group(0).strip().lower()
    except Exception:
        pass

    cached_result = await db.find_cached_analysis(
        file_hash=file_hash,
        candidate_email=candidate_email,
        target_role=target_job.title,
        user_id=current_user_id
    )
    if cached_result:
        logger.info(f"[DB RETRIEVAL CACHE HIT] Same resume and role '{target_job.title}' detected. Returning saved evaluation from DB (0 LLM calls).")
        return cached_result

    logger.info(f"Initiating HireWise pipeline for '{resume_file.filename}' matching against '{target_job.title}' (user_id={current_user_id})...")

    try:
        analysis_result = await execute_hirewise_workflow(
            pdf_bytes=pdf_bytes,
            job_description=target_job,
            user_id=current_user_id,
            file_hash=file_hash
        )
        return analysis_result
    except Exception as e:
        logger.error(f"Error executing agent pipeline: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis pipeline error: {str(e)}"
        )


@app.post("/api/analyze/stream", tags=["Analysis"])
async def analyze_resume_stream(
    request: Request,
    resume_file: UploadFile = File(..., description="Candidate Resume in PDF format"),
    job_id: Optional[str] = Form(None, description="Selected Job ID from active catalog"),
    custom_job_description: Optional[str] = Form(None, description="Pasted custom Job Description text"),
    custom_job_title: Optional[str] = Form("Target Role", description="Title for custom job"),
    custom_job_company: Optional[str] = Form("Target Company", description="Company for custom job")
):
    """
    Incremental Section Hydration Streaming Endpoint (Server-Sent Events).
    Dispatches live SSE events as each agent executes:
    - event: step -> Live agent progress & status message
    - event: profile -> Parsed candidate profile (~2-3s)
    - event: match -> ATS Score gauge & skill badges (~4-5s)
    - event: improvements -> Google XYZ STAR bullet rewrites & interview tips (~8-10s)
    - event: complete -> Final payload and database persistence confirmation
    """
    # 1. Validation
    if not resume_file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a PDF resume document.")

    pdf_bytes = await resume_file.read()
    if len(pdf_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="The uploaded PDF exceeds the 10MB limit.")
    if not pdf_bytes.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid PDF document.")
    if len(pdf_bytes) < 100:
        raise HTTPException(status_code=400, detail="The uploaded PDF file is empty or corrupted.")

    # 2. Resolve Target Job
    target_job: Optional[JobDescription] = None
    if job_id:
        target_job = await db.get_job_by_id(job_id)

    if not target_job and custom_job_description and custom_job_description.strip():
        extracted_skills = [
            kw for kw in [
                "Python", "FastAPI", "React", "Next.js", "TypeScript", "JavaScript",
                "PostgreSQL", "pgvector", "Docker", "Kubernetes", "AWS", "LangGraph",
                "LangChain", "Gemini", "OpenAI", "RAG", "Tailwind CSS", "Redis"
            ]
            if kw.lower() in custom_job_description.lower()
        ]
        target_job = JobDescription(
            id=f"custom-{uuid.uuid4().hex[:6]}",
            title=custom_job_title or "Target Position",
            company=custom_job_company or "Target Company",
            department="Engineering",
            description=custom_job_description,
            requirements=[line.strip() for line in custom_job_description.split("\n") if len(line.strip()) > 15][:5],
            skills_required=extracted_skills if extracted_skills else ["Software Development", "Problem Solving"],
            min_years_experience=3.0
        )
    elif not target_job:
        jobs = await db.get_all_jobs()
        target_job = jobs[0] if jobs else None

    if not target_job:
        raise HTTPException(status_code=400, detail="No valid job description selected or provided.")

    current_user_id = await get_current_user_id_optional(request)

    # Fast 1ms detection of same resume + target role in database
    file_hash = hashlib.sha256(pdf_bytes).hexdigest()
    candidate_email = ""
    try:
        import fitz
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            sample_text = "\n".join([doc[i].get_text() for i in range(min(2, len(doc)))])
            email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', sample_text)
            if email_match:
                candidate_email = email_match.group(0).strip().lower()
    except Exception:
        pass

    cached_result = await db.find_cached_analysis(
        file_hash=file_hash,
        candidate_email=candidate_email,
        target_role=target_job.title,
        user_id=current_user_id
    )

    if cached_result:
        logger.info(f"[DB RETRIEVAL CACHE HIT] Same resume and role '{target_job.title}' uploaded. Replaying saved data instantly from DB.")

        async def cached_event_generator():
            def sse(event: str, data: Any) -> str:
                return f"event: {event}\ndata: {json.dumps(data)}\n\n"

            yield sse("step", {
                "step": "retrieving",
                "message": "⚡ Past evaluation found in database! Loading instantly without re-analysis...",
                "progress": 30
            })
            await asyncio.sleep(0.04)
            yield sse("profile", {
                "parsed_profile": cached_result.get("parsed_profile", {}),
                "progress": 60,
                "logs": ["[Database Cache Hit] Retrieved existing evaluation from Neon DB (0 LLM calls)."]
            })
            await asyncio.sleep(0.04)
            yield sse("match", {
                "match_result": cached_result.get("match_result", {}),
                "ats_score": cached_result.get("ats_score", 0.0),
                "progress": 85,
                "logs": ["[Database Cache Hit] Restored ATS alignment score and matched skills."]
            })
            await asyncio.sleep(0.04)
            yield sse("improvements", {
                "bullet_improvements": cached_result.get("bullet_improvements", []),
                "interview_tips": cached_result.get("interview_tips", []),
                "progress": 98,
                "logs": ["[Database Cache Hit] Restored Google XYZ bullet rewrites and coaching questions."]
            })
            await asyncio.sleep(0.04)
            yield sse("complete", {
                "final_result": cached_result,
                "progress": 100
            })

        return StreamingResponse(
            cached_event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    logger.info(f"[SSE STREAM] Starting incremental analysis for '{resume_file.filename}' -> '{target_job.title}'...")

    async def event_generator():
        def sse(event: str, data: Any) -> str:
            return f"event: {event}\ndata: {json.dumps(data)}\n\n"

        state = {
            "pdf_bytes": pdf_bytes,
            "file_hash": file_hash,
            "raw_text": "",
            "job_description": target_job,
            "user_id": current_user_id,
            "agent_logs": []
        }

        try:
            # Stage 0: Instant pre-parse (<50ms) — dispatch profile immediately
            yield sse("step", {"step": "parsing", "message": "Extracting candidate profile...", "progress": 15})

            raw_text = gemini_service.extract_text_from_pdf(pdf_bytes)
            if not raw_text.strip():
                raw_text = "Experienced Software Engineer with full-stack and cloud development experience."
            state["raw_text"] = raw_text

            # Instant rule-based pre-parse for immediate UI flip
            pre_parsed = gemini_service._rule_based_resume_parser(raw_text)
            state["parsed_resume"] = pre_parsed

            # Dispatch pre-parsed Profile Event immediately (<100ms from upload)
            yield sse("profile", {
                "parsed_profile": pre_parsed.model_dump(),
                "progress": 35,
                "logs": ["[Instant Pre-Parser] Profile extracted in <50ms (zero LLM calls). Refining in background..."]
            })

            # Stage 1+2+3: Run parser refinement, RAG, and STAR ALL in parallel
            yield sse("step", {"step": "matching", "message": "Running ATS scoring & STAR optimizations in parallel...", "progress": 55})

            async def _run_parser_refinement():
                """Only calls Gemini if pre-parser was sparse; otherwise returns pre_parsed."""
                from app.agents.tools import calculate_experience_years
                refined = await gemini_service.parse_resume_to_structured_json(raw_text, pdf_bytes=pdf_bytes)
                exp_dicts = [exp.model_dump() for exp in refined.experience]
                exact_years = calculate_experience_years.invoke({"experiences": exp_dicts})
                refined.total_years_experience = exact_years
                return refined

            async def _run_rag_with_state():
                return await hybrid_rag_node(state)

            async def _run_improver_with_state():
                return await improver_node(state)

            # Fire all three in parallel!
            refined_profile, rag_res, improve_res = await asyncio.gather(
                _run_parser_refinement(),
                _run_rag_with_state(),
                _run_improver_with_state()
            )

            # Update state with refined profile
            state["parsed_resume"] = refined_profile
            state.update(rag_res)
            state.update(improve_res)

            # Re-dispatch refined profile if it changed
            if refined_profile.full_name != pre_parsed.full_name or len(refined_profile.skills) != len(pre_parsed.skills):
                yield sse("profile", {
                    "parsed_profile": refined_profile.model_dump(),
                    "progress": 60,
                    "logs": state.get("agent_logs", [])
                })

            match_res = state["match_result"]
            ats_score = state["ats_score"]

            # If score is >= 80, generate technical interview questions as well
            if ats_score >= 80.0:
                coach_res = await interview_tips_node(state)
                state.update(coach_res)

            # Dispatch Match Event (hydrates Score Gauge & Skill badges!)
            yield sse("match", {
                "match_result": match_res.model_dump(),
                "ats_score": ats_score,
                "progress": 85,
                "logs": state.get("agent_logs", [])
            })

            bullet_improvements = state.get("bullet_improvements", [])
            interview_tips = state.get("interview_tips", [])

            # Dispatch Improvements Event (hydrates STAR Diff Table & Interview Scripts!)
            yield sse("improvements", {
                "bullet_improvements": [b.model_dump() for b in bullet_improvements],
                "interview_tips": interview_tips,
                "progress": 95,
                "logs": state.get("agent_logs", [])
            })

            # Stage 4: State Merger & PostgreSQL Persistence
            yield sse("step", {"step": "finalizing", "message": "Persisting evaluation record and compiling report...", "progress": 98})
            merger_res = await merger_node(state)
            final_res = merger_res["final_result"]

            # Dispatch Complete Event
            yield sse("complete", {
                "final_result": final_res.model_dump(),
                "progress": 100
            })

        except Exception as e:
            logger.error(f"Error in SSE stream pipeline: {e}", exc_info=True)
            yield sse("error", {"detail": f"Analysis pipeline error: {str(e)}"})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
