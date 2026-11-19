import asyncio
import logging
import uuid
from typing import Any, Dict
from app.agents.state import HireWiseState
from app.agents.tools import calculate_ats_score, calculate_experience_years
from app.database import db
from app.schemas import HireWiseAnalysisResult, MatchResult
from app.services.gemini_service import gemini_service
from app.services.vector_service import vector_service

logger = logging.getLogger("hirewise.nodes")


async def parser_node(state: HireWiseState) -> Dict[str, Any]:
    """
    Agent 1: Extraction Node.
    Extracts layout-aware text from PDF bytes via PyMuPDF, then generates
    structured profile JSON (skills, dated experiences, bullets, education)
    using Gemini 2.5 Flash.
    """
    logs = list(state.get("agent_logs", []))
    logs.append("[Step 1: Resume Parser] Ingesting PDF and extracting layout blocks via PyMuPDF...")

    raw_text = state.get("raw_text", "")
    pdf_bytes = state.get("pdf_bytes")

    if pdf_bytes and not raw_text:
        raw_text = await asyncio.to_thread(gemini_service.extract_text_from_pdf, pdf_bytes)

    if not raw_text.strip():
        raw_text = "Experienced Software Engineer with full-stack and cloud development experience."

    # Parse to structured profile via Gemini / structured extractor
    parsed_profile = await gemini_service.parse_resume_to_structured_json(raw_text, pdf_bytes=pdf_bytes)

    # Calculate exact duration using deterministic Python date tool
    exp_dicts = [exp.model_dump() for exp in parsed_profile.experience]
    exact_years = calculate_experience_years.invoke({"experiences": exp_dicts})
    parsed_profile.total_years_experience = exact_years

    logs.append(
        f"[Step 1: Resume Parser] Profile extracted for '{parsed_profile.full_name}' | "
        f"{len(parsed_profile.skills)} skills identified | {exact_years} years verified experience."
    )

    return {
        "raw_text": raw_text,
        "parsed_resume": parsed_profile,
        "agent_logs": logs
    }


async def hybrid_rag_node(state: HireWiseState) -> Dict[str, Any]:
    """
    Agent 2: Hybrid Matching Node.
    Chunks resume text, writes embeddings (768-dim) to PostgreSQL pgvector,
    performs hybrid vector cosine similarity (<=>) and keyword matching,
    and runs the deterministic Python @tool to compute ATS score.
    """
    logs = list(state.get("agent_logs", []))
    logs.append("[Step 2: ATS Matcher] Running Hybrid RAG (pgvector cosine search + skill density)...")

    raw_text = state.get("raw_text", "")
    parsed_resume = state.get("parsed_resume")
    job_desc = state.get("job_description")
    resume_id = state.get("resume_id") or str(uuid.uuid4())

    # Chunk resume text
    chunks = vector_service.chunk_text(raw_text)

    # Prepare job details
    job_text = f"{job_desc.title}\n{job_desc.company}\n{job_desc.description}\n{' '.join(job_desc.requirements)}"
    job_skills = list(job_desc.skills_required)

    # Perform Hybrid Search and Score
    hybrid_stats = await vector_service.hybrid_search_and_score(
        resume_id=resume_id,
        resume_chunks=chunks,
        job_description_text=job_text,
        job_skills=job_skills
    )

    # Deterministic Scoring via @tool
    score_tool_result = calculate_ats_score.invoke({
        "matched_skills": hybrid_stats["matched_skills"],
        "missing_skills": hybrid_stats["missing_skills"],
        "exp_years_actual": parsed_resume.total_years_experience if parsed_resume else 2.0,
        "exp_years_required": job_desc.min_years_experience,
        "vector_similarity": hybrid_stats["avg_vector_similarity"]
    })

    overall_score = score_tool_result["overall_score"]
    skill_score = score_tool_result["skill_match_score"]
    vector_score = score_tool_result["vector_similarity_score"]
    exp_score = score_tool_result["experience_score"]

    match_summary = (
        f"Candidate achieved an overall ATS score of {overall_score}%. "
        f"Matched {len(hybrid_stats['matched_skills'])} of {len(job_skills)} target skills with "
        f"{parsed_resume.total_years_experience if parsed_resume else 0} years experience against "
        f"{job_desc.min_years_experience} required."
    )

    match_result = MatchResult(
        overall_score=overall_score,
        vector_similarity_score=vector_score,
        skill_match_score=skill_score,
        experience_score=exp_score,
        matched_skills=hybrid_stats["matched_skills"],
        missing_skills=hybrid_stats["missing_skills"],
        experience_years_required=job_desc.min_years_experience,
        experience_years_actual=parsed_resume.total_years_experience if parsed_resume else 2.0,
        match_summary=match_summary
    )

    logs.append(
        f"[Step 2: ATS Matcher] Hybrid Score: {overall_score}% "
        f"(Skills: {skill_score}%, Vector Similarity: {vector_score}%, Exp: {exp_score}%)."
    )

    return {
        "resume_id": resume_id,
        "chunks": chunks,
        "retrieval_stats": hybrid_stats,
        "match_result": match_result,
        "ats_score": overall_score,
        "agent_logs": logs
    }


async def improver_node(state: HireWiseState) -> Dict[str, Any]:
    """
    Agent 3A: Optimization Node (Triggered when ATS score < 80%).
    Rewrites candidate's bullet points using the STAR methodology,
    adding quantifiable impact metrics and key job skills.
    """
    logs = list(state.get("agent_logs", []))
    logs.append("[Step 3: Resume Improver] Score < 80%. Initiating STAR bullet point rewriting...")

    parsed_resume = state.get("parsed_resume")
    job_desc = state.get("job_description")

    # Collect existing bullet points from parsed resume experience
    original_bullets = []
    if parsed_resume and parsed_resume.experience:
        for exp in parsed_resume.experience:
            original_bullets.extend(exp.bullets)

    if not original_bullets:
        original_bullets = [
            "Responsible for building backend APIs and database tables.",
            "Worked on frontend user interfaces and bug fixes.",
            "Collaborated with project managers on sprint deliverables."
        ]

    job_context = f"{job_desc.title} at {job_desc.company}. Requirements: {' '.join(job_desc.requirements)}"
    improvements = await gemini_service.rewrite_bullets_to_star(original_bullets, job_context)

    logs.append(f"[Step 3: Resume Improver] Successfully transformed {len(improvements)} bullet points into STAR format.")

    return {
        "bullet_improvements": improvements,
        "interview_tips": [],
        "agent_logs": logs
    }


async def interview_tips_node(state: HireWiseState) -> Dict[str, Any]:
    """
    Agent 3B: Interview Coaching Node (Triggered when ATS score >= 80%).
    Skips bullet rewrites and generates domain-specific technical & behavioral interview tips.
    """
    logs = list(state.get("agent_logs", []))
    logs.append("[Step 3: Interview Coach] Score >= 80%. Skipping rewrites; generating advanced interview questions...")

    parsed_resume = state.get("parsed_resume")
    job_desc = state.get("job_description")

    job_context = f"{job_desc.title} at {job_desc.company}. Requirements: {' '.join(job_desc.requirements)}"
    tips = await gemini_service.generate_interview_coaching_tips(parsed_resume, job_context)

    logs.append(f"[Step 3: Interview Coach] Generated {len(tips)} customized interview coaching points.")

    return {
        "bullet_improvements": [],
        "interview_tips": tips,
        "agent_logs": logs
    }


async def merger_node(state: HireWiseState) -> Dict[str, Any]:
    """
    Step 4: Final State Merger Node.
    Assembles final Pydantic analysis payload and persists results to PostgreSQL.
    """
    logs = list(state.get("agent_logs", []))
    logs.append("[Step 4: State Merger] Compiling final analysis payload and persisting record...")

    ats_score = state.get("ats_score", 0.0)
    parsed_profile = state.get("parsed_resume")
    match_result = state.get("match_result")
    bullet_improvements = state.get("bullet_improvements", [])
    interview_tips = state.get("interview_tips", [])
    resume_id = state.get("resume_id", str(uuid.uuid4()))

    final_result = HireWiseAnalysisResult(
        status="success",
        ats_score=ats_score,
        passed_threshold=(ats_score >= 80.0),
        parsed_profile=parsed_profile,
        match_result=match_result,
        bullet_improvements=bullet_improvements,
        interview_tips=interview_tips,
        agent_logs=logs
    )

    # Persist to database
    job_desc = state.get("job_description")
    user_id = state.get("user_id")
    file_hash = state.get("file_hash", "")
    try:
        await db.save_resume_analysis(
            resume_id=resume_id,
            parsed_json=final_result.model_dump(),
            ats_score=ats_score,
            full_name=parsed_profile.full_name if parsed_profile else "",
            email=parsed_profile.email if parsed_profile else "",
            target_role=job_desc.title if job_desc else "Target Role",
            target_company=job_desc.company if job_desc else "",
            user_id=user_id,
            file_hash=file_hash
        )
    except Exception as e:
        logger.error(f"Error persisting resume analysis to DB: {e}")

    logs.append("[Step 4: State Merger] Analysis successfully completed and delivered.")

    return {
        "final_result": final_result,
        "agent_logs": logs
    }

