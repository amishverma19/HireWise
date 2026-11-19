import asyncio
from datetime import datetime, timezone
import json
import logging
import os
import sys
import uuid
from typing import Any, Dict, List, Optional
import psycopg
from psycopg.rows import dict_row
import psycopg_pool
from pgvector.psycopg import register_vector_async

from app.config import get_settings
from app.schemas import JobDescription

logger = logging.getLogger("hirewise.database")

# Fix for Windows event loop with psycopg async if needed
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass


class DatabaseManager:
    """
    Manages PostgreSQL connection pool with pgvector support via psycopg 3 async.
    Provides graceful fallback to in-memory store if DB is unreachable.
    Includes pool connection validation and lifetime cycling for serverless Neon DB.
    """
    def __init__(self):
        self._pool: Optional[psycopg_pool.AsyncConnectionPool] = None
        self._is_connected = False
        self._in_memory_jobs: Dict[str, JobDescription] = {}
        self._in_memory_analyses: Dict[str, Dict[str, Any]] = {}
        self._in_memory_users: Dict[str, Dict[str, Any]] = {}

    async def _configure_connection(self, conn: psycopg.AsyncConnection):
        """Register pgvector types on each newly opened connection."""
        await register_vector_async(conn)

    async def connect(self):
        settings = get_settings()
        db_url = settings.DATABASE_URL
        if not db_url:
            logger.warning("DATABASE_URL is not configured. Running in in-memory fallback mode.")
            self._seed_in_memory_jobs()
            return

        # Normalize postgresql+psycopg:// to postgresql:// for psycopg pool
        clean_url = db_url.replace("postgresql+psycopg://", "postgresql://").replace("postgres://", "postgresql://")

        try:
            logger.info("Initializing PostgreSQL connection pool with pgvector and socket checks...")
            self._pool = psycopg_pool.AsyncConnectionPool(
                conninfo=clean_url,
                min_size=1,
                max_size=10,
                open=False,
                configure=self._configure_connection,
                check=psycopg_pool.AsyncConnectionPool.check_connection,
                max_idle=60.0,
                max_lifetime=300.0,
                timeout=15.0
            )
            await self._pool.open()
            self._is_connected = True
            logger.info("Connected successfully to PostgreSQL (Neon DB).")

            # Initialize extensions and schema
            await self.init_db()
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}. Falling back to in-memory mode.")
            self._is_connected = False
            self._seed_in_memory_jobs()

    async def disconnect(self):
        if self._pool and self._is_connected:
            await self._pool.close()
            self._is_connected = False
            logger.info("PostgreSQL connection pool closed.")

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    async def init_db(self):
        """Creates pgvector extension, users, jobs, resumes, and vector tables."""
        if not self._is_connected or not self._pool:
            self._seed_in_memory_jobs()
            return

        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                # 1. Enable pgvector extension
                await cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

                # 2. Users Table for Authentication
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        hashed_password TEXT NOT NULL,
                        full_name TEXT DEFAULT '',
                        reset_code TEXT DEFAULT '',
                        reset_expires_at TIMESTAMP WITH TIME ZONE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                await cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_code TEXT DEFAULT '';")
                await cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_expires_at TIMESTAMP WITH TIME ZONE;")

                # 3. Job Descriptions Table
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS job_descriptions (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        company TEXT NOT NULL,
                        department TEXT DEFAULT 'Engineering',
                        description TEXT NOT NULL,
                        requirements JSONB DEFAULT '[]'::jsonb,
                        skills_required JSONB DEFAULT '[]'::jsonb,
                        min_years_experience REAL DEFAULT 2.0,
                        embedding vector(768),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # 4. Resumes Table
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS resumes (
                        id TEXT PRIMARY KEY,
                        user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                        full_name TEXT DEFAULT '',
                        email TEXT DEFAULT '',
                        phone TEXT DEFAULT '',
                        target_role TEXT DEFAULT '',
                        target_company TEXT DEFAULT '',
                        parsed_json JSONB DEFAULT '{}'::jsonb,
                        ats_score REAL DEFAULT 0.0,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                await cur.execute("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS target_role TEXT DEFAULT '';")
                await cur.execute("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS target_company TEXT DEFAULT '';")
                await cur.execute("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS user_id TEXT REFERENCES users(id) ON DELETE CASCADE;")
                await cur.execute("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS file_hash TEXT DEFAULT '';")
                await cur.execute("CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);")
                await cur.execute("CREATE INDEX IF NOT EXISTS idx_resumes_file_hash ON resumes(file_hash);")
                await cur.execute("CREATE INDEX IF NOT EXISTS idx_resumes_hash_role ON resumes(file_hash, target_role);")

                # 5. Resume Chunks Table for pgvector similarity search
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS resume_chunks (
                        id TEXT PRIMARY KEY,
                        resume_id TEXT REFERENCES resumes(id) ON DELETE CASCADE,
                        chunk_index INT NOT NULL,
                        chunk_text TEXT NOT NULL,
                        embedding vector(768)
                    );
                """)

                await conn.commit()
                logger.info("Database tables and indexes initialized.")

        # Seed initial job openings
        await self.seed_initial_jobs()

    # --- User Management Operations ---

    async def create_user(self, email: str, hashed_password: str, full_name: str = "") -> Dict[str, Any]:
        """Creates a new user record in the database."""
        user_id = f"user-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        user_data = {
            "id": user_id,
            "email": email.lower().strip(),
            "hashed_password": hashed_password,
            "full_name": full_name,
            "reset_code": "",
            "reset_expires_at": None,
            "created_at": now.strftime("%b %d, %Y")
        }
        self._in_memory_users[user_id] = user_data

        if self._is_connected and self._pool:
            async with self._pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute("""
                        INSERT INTO users (id, email, hashed_password, full_name)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id, email, full_name, to_char(created_at, 'Mon DD, YYYY') as created_at;
                    """, (user_id, email.lower().strip(), hashed_password, full_name))
                    row = await cur.fetchone()
                    await conn.commit()
                    if row:
                        return dict(row)

        return {
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "created_at": now.strftime("%b %d, %Y")
        }

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieves a user by email address."""
        clean_email = email.lower().strip()
        if not self._is_connected or not self._pool:
            for u in self._in_memory_users.values():
                if u["email"].lower() == clean_email:
                    return u
            return None

        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute("""
                    SELECT id, email, hashed_password, full_name, reset_code, reset_expires_at,
                           to_char(created_at, 'Mon DD, YYYY') as created_at
                    FROM users
                    WHERE LOWER(email) = %s;
                """, (clean_email,))
                row = await cur.fetchone()
                return dict(row) if row else None

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves user profile by user ID."""
        if not self._is_connected or not self._pool:
            return self._in_memory_users.get(user_id)

        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute("""
                    SELECT id, email, full_name, to_char(created_at, 'Mon DD, YYYY') as created_at
                    FROM users
                    WHERE id = %s;
                """, (user_id,))
                row = await cur.fetchone()
                return dict(row) if row else None

    async def set_reset_code(self, email: str, code: str, expires_at: datetime) -> bool:
        """Saves a 6-digit password reset code with expiration."""
        clean_email = email.lower().strip()
        for u in self._in_memory_users.values():
            if u["email"].lower() == clean_email:
                u["reset_code"] = code
                u["reset_expires_at"] = expires_at

        if self._is_connected and self._pool:
            async with self._pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("""
                        UPDATE users
                        SET reset_code = %s, reset_expires_at = %s
                        WHERE LOWER(email) = %s;
                    """, (code, expires_at, clean_email))
                    await conn.commit()
                    return cur.rowcount > 0
        return True

    async def verify_reset_code(self, email: str, code: str) -> bool:
        """Verifies if the reset code matches and has not expired (without resetting yet)."""
        clean_email = email.lower().strip()
        now = datetime.now(timezone.utc)

        if not self._is_connected or not self._pool:
            for u in self._in_memory_users.values():
                if u["email"].lower() == clean_email:
                    return (
                        u.get("reset_code") == code
                        and u.get("reset_expires_at") is not None
                        and u["reset_expires_at"] > now
                    )
            return False

        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute("""
                    SELECT reset_code, reset_expires_at
                    FROM users
                    WHERE LOWER(email) = %s;
                """, (clean_email,))
                row = await cur.fetchone()
                if not row or not row.get("reset_code"):
                    return False

                if row["reset_code"] != code:
                    return False

                exp = row["reset_expires_at"]
                if exp and exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)

                if exp and exp < now:
                    return False
                return True

    async def verify_and_reset_password(self, email: str, code: str, new_hashed_password: str) -> bool:
        """Verifies reset code and updates password hash."""
        clean_email = email.lower().strip()
        now = datetime.now(timezone.utc)

        if not self._is_connected or not self._pool:
            for u in self._in_memory_users.values():
                if u["email"].lower() == clean_email:
                    if u.get("reset_code") == code and u.get("reset_expires_at") and u["reset_expires_at"] > now:
                        u["hashed_password"] = new_hashed_password
                        u["reset_code"] = ""
                        u["reset_expires_at"] = None
                        return True
            return False

        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute("""
                    SELECT reset_code, reset_expires_at
                    FROM users
                    WHERE LOWER(email) = %s;
                """, (clean_email,))
                row = await cur.fetchone()
                if not row or not row.get("reset_code"):
                    return False

                if row["reset_code"] != code:
                    return False

                exp = row["reset_expires_at"]
                if exp and exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)

                if exp and exp < now:
                    return False

                await cur.execute("""
                    UPDATE users
                    SET hashed_password = %s, reset_code = '', reset_expires_at = NULL
                    WHERE LOWER(email) = %s;
                """, (new_hashed_password, clean_email))
                await conn.commit()
                return True

    # --- Job Operations ---

    def _seed_in_memory_jobs(self):
        defaults = self._get_default_jobs()
        for job in defaults:
            self._in_memory_jobs[job.id] = job

    def _get_default_jobs(self) -> List[JobDescription]:
        return [
            JobDescription(
                id="job-senior-fullstack",
                title="Senior Full-Stack Engineer",
                company="HireWise Tech Labs",
                department="Platform Core",
                description="We are seeking an experienced Senior Full-Stack Engineer to build scalable cloud applications, leading TypeScript/React frontends and high-performance Python/FastAPI microservices backed by PostgreSQL and pgvector.",
                requirements=[
                    "Design and implement responsive web applications using Next.js, React, and Tailwind CSS",
                    "Architect RESTful and streaming APIs with Python (FastAPI/Pydantic) and asynchronous event processing",
                    "Manage PostgreSQL databases, schema migrations, and vector similarity search with pgvector",
                    "Deploy microservices with Docker, Kubernetes, and modern CI/CD pipelines",
                    "Mentor junior developers and participate in rigorous code reviews"
                ],
                skills_required=[
                    "React", "Next.js", "TypeScript", "Python", "FastAPI",
                    "PostgreSQL", "pgvector", "Docker", "Tailwind CSS", "REST APIs", "Git"
                ],
                min_years_experience=4.0
            ),
            JobDescription(
                id="job-ai-agent-engineer",
                title="AI & Multi-Agent Systems Engineer",
                company="Cognitive Dynamics",
                department="Applied AI",
                description="Join our elite AI research & engineering unit to build state-of-the-art autonomous multi-agent pipelines using LangGraph, Google Gemini models, hybrid RAG retrieval, and vector embeddings.",
                requirements=[
                    "Design and develop complex agentic workflows using LangGraph and stateful orchestrators",
                    "Implement Hybrid RAG pipelines combining dense vector similarity with sparse BM25/keyword retrieval",
                    "Integrate Google Gemini Flash and File API for multimodal document processing",
                    "Build automated evaluation benchmarks, latency optimizations, and agent guardrails",
                    "Work with PostgreSQL, pgvector, and distributed caching systems"
                ],
                skills_required=[
                    "Python", "LangGraph", "LangChain", "Gemini API", "LLMs",
                    "RAG", "pgvector", "Vector Search", "FastAPI", "Prompt Engineering", "PyMuPDF"
                ],
                min_years_experience=3.0
            ),
            JobDescription(
                id="job-staff-backend-engineer",
                title="Staff Backend Systems Engineer",
                company="Nexus Distributed Labs",
                department="Infrastructure",
                description="Looking for a Staff Backend Engineer to drive architectural decisions across high-throughput distributed systems, event-driven data pipelines, and database optimization.",
                requirements=[
                    "Architect mission-critical distributed services processing millions of daily transactions",
                    "Lead database performance tuning, indexing strategies, and connection pooling across PostgreSQL clusters",
                    "Design fault-tolerant event streams with Kafka or RabbitMQ",
                    "Champion engineering best practices, security standards, and observability (OpenTelemetry)",
                    "Collaborate with product and executive leadership on technical strategy"
                ],
                skills_required=[
                    "Python", "PostgreSQL", "Distributed Systems", "Redis", "Kafka",
                    "Docker", "Kubernetes", "Linux", "System Architecture", "Performance Tuning"
                ],
                min_years_experience=6.0
            )
        ]

    async def seed_initial_jobs(self):
        """Seeds default tech jobs in PostgreSQL if table is empty."""
        if not self._is_connected or not self._pool:
            return

        default_jobs = self._get_default_jobs()
        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute("SELECT COUNT(*) as count FROM job_descriptions;")
                row = await cur.fetchone()
                if row and row["count"] == 0:
                    logger.info("Seeding initial job openings into PostgreSQL...")
                    for job in default_jobs:
                        await cur.execute("""
                            INSERT INTO job_descriptions 
                            (id, title, company, department, description, requirements, skills_required, min_years_experience)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO NOTHING;
                        """, (
                            job.id,
                            job.title,
                            job.company,
                            job.department,
                            job.description,
                            json.dumps(job.requirements),
                            json.dumps(job.skills_required),
                            job.min_years_experience
                        ))
                    await conn.commit()

    async def get_all_jobs(self) -> List[JobDescription]:
        """Fetch all job openings from database or in-memory fallback."""
        if not self._is_connected or not self._pool:
            return list(self._in_memory_jobs.values())

        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute("""
                    SELECT id, title, company, department, description, requirements, skills_required, min_years_experience 
                    FROM job_descriptions ORDER BY created_at DESC;
                """)
                rows = await cur.fetchall()
                jobs = []
                for r in rows:
                    reqs = r["requirements"] if isinstance(r["requirements"], list) else json.loads(r["requirements"] or "[]")
                    skills = r["skills_required"] if isinstance(r["skills_required"], list) else json.loads(r["skills_required"] or "[]")
                    jobs.append(JobDescription(
                        id=r["id"],
                        title=r["title"],
                        company=r["company"],
                        department=r.get("department", "Engineering"),
                        description=r["description"],
                        requirements=reqs,
                        skills_required=skills,
                        min_years_experience=float(r.get("min_years_experience", 2.0))
                    ))
                return jobs

    async def get_job_by_id(self, job_id: str) -> Optional[JobDescription]:
        """Fetch a specific job description by ID."""
        if not self._is_connected or not self._pool:
            return self._in_memory_jobs.get(job_id)

        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute("""
                    SELECT id, title, company, department, description, requirements, skills_required, min_years_experience 
                    FROM job_descriptions WHERE id = %s;
                """, (job_id,))
                r = await cur.fetchone()
                if not r:
                    return self._in_memory_jobs.get(job_id)

                reqs = r["requirements"] if isinstance(r["requirements"], list) else json.loads(r["requirements"] or "[]")
                skills = r["skills_required"] if isinstance(r["skills_required"], list) else json.loads(r["skills_required"] or "[]")
                return JobDescription(
                    id=r["id"],
                    title=r["title"],
                    company=r["company"],
                    department=r.get("department", "Engineering"),
                    description=r["description"],
                    requirements=reqs,
                    skills_required=skills,
                    min_years_experience=float(r.get("min_years_experience", 2.0))
                )

    async def save_job(self, job: JobDescription) -> JobDescription:
        """Saves a new job description."""
        self._in_memory_jobs[job.id] = job
        if self._is_connected and self._pool:
            async with self._pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("""
                        INSERT INTO job_descriptions 
                        (id, title, company, department, description, requirements, skills_required, min_years_experience)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            title = EXCLUDED.title,
                            company = EXCLUDED.company,
                            description = EXCLUDED.description,
                            requirements = EXCLUDED.requirements,
                            skills_required = EXCLUDED.skills_required,
                            min_years_experience = EXCLUDED.min_years_experience;
                    """, (
                        job.id, job.title, job.company, job.department,
                        job.description, json.dumps(job.requirements),
                        json.dumps(job.skills_required), job.min_years_experience
                    ))
                    await conn.commit()
        return job

    # --- Resume Analysis & Scoped History Operations ---

    async def save_resume_analysis(
        self,
        resume_id: str,
        parsed_json: dict,
        ats_score: float,
        full_name: str = "",
        email: str = "",
        target_role: str = "",
        target_company: str = "",
        user_id: Optional[str] = None,
        file_hash: str = ""
    ):
        """Saves resume analysis record to DB bound to authenticated user_id with file_hash cache key."""
        self._in_memory_analyses[resume_id] = {
            "id": resume_id,
            "user_id": user_id,
            "full_name": full_name,
            "email": email,
            "target_role": target_role,
            "target_company": target_company,
            "parsed_json": parsed_json,
            "ats_score": ats_score,
            "file_hash": file_hash,
            "created_at": "Just now"
        }

        if not self._is_connected or not self._pool:
            return

        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    INSERT INTO resumes (id, user_id, full_name, email, target_role, target_company, parsed_json, ats_score, file_hash)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        user_id = COALESCE(EXCLUDED.user_id, resumes.user_id),
                        full_name = EXCLUDED.full_name,
                        email = EXCLUDED.email,
                        target_role = EXCLUDED.target_role,
                        target_company = EXCLUDED.target_company,
                        parsed_json = EXCLUDED.parsed_json,
                        ats_score = EXCLUDED.ats_score,
                        file_hash = EXCLUDED.file_hash;
                """, (resume_id, user_id, full_name, email, target_role, target_company, json.dumps(parsed_json), ats_score, file_hash))
                await conn.commit()

    async def find_cached_analysis(
        self,
        file_hash: str,
        candidate_email: str = "",
        target_role: str = "",
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves a previously computed evaluation record for the same resume and target role.
        Zero Gemini LLM calls - returns immediately from PostgreSQL or in-memory cache.
        Matches by:
        1. Exact PDF file hash + target role (case-insensitive)
        2. Candidate email (extracted from resume) + target role
        3. If user_id provided, prioritizes/associates with authenticated user.
        """
        normalized_role = (target_role or "").strip().lower()

        # 1. Check in-memory store
        for item in reversed(list(self._in_memory_analyses.values())):
            item_role = (item.get("target_role") or "").strip().lower()
            if item_role == normalized_role:
                if (file_hash and item.get("file_hash") == file_hash) or \
                   (candidate_email and item.get("email", "").lower() == candidate_email.lower()):
                    data = item.get("parsed_json")
                    if data:
                        return data if isinstance(data, dict) else json.loads(data)

        if not self._is_connected or not self._pool:
            return None

        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                # 2. Match exact file_hash + target_role
                if file_hash:
                    await cur.execute("""
                        SELECT id, user_id, parsed_json 
                        FROM resumes 
                        WHERE file_hash = %s AND LOWER(TRIM(target_role)) = LOWER(TRIM(%s))
                        ORDER BY created_at DESC 
                        LIMIT 1;
                    """, (file_hash, target_role))
                    row = await cur.fetchone()
                    if row and row.get("parsed_json"):
                        if user_id and not row.get("user_id"):
                            await cur.execute("UPDATE resumes SET user_id = %s WHERE id = %s;", (user_id, row["id"]))
                            await conn.commit()
                        data = row["parsed_json"]
                        return data if isinstance(data, dict) else json.loads(data)

                # 3. Fallback: Match by candidate email extracted from resume + target_role
                if candidate_email and len(candidate_email) > 4:
                    if user_id:
                        await cur.execute("""
                            SELECT id, user_id, parsed_json 
                            FROM resumes 
                            WHERE LOWER(TRIM(email)) = LOWER(TRIM(%s)) 
                              AND LOWER(TRIM(target_role)) = LOWER(TRIM(%s))
                              AND (user_id = %s OR user_id IS NULL)
                            ORDER BY created_at DESC 
                            LIMIT 1;
                        """, (candidate_email, target_role, user_id))
                    else:
                        await cur.execute("""
                            SELECT id, user_id, parsed_json 
                            FROM resumes 
                            WHERE LOWER(TRIM(email)) = LOWER(TRIM(%s)) 
                              AND LOWER(TRIM(target_role)) = LOWER(TRIM(%s))
                            ORDER BY created_at DESC 
                            LIMIT 1;
                        """, (candidate_email, target_role))
                    row = await cur.fetchone()
                    if row and row.get("parsed_json"):
                        # Backfill file_hash and user_id for future instant hits
                        updates = []
                        params = []
                        if file_hash:
                            updates.append("file_hash = %s")
                            params.append(file_hash)
                        if user_id and not row.get("user_id"):
                            updates.append("user_id = %s")
                            params.append(user_id)
                        if updates:
                            params.append(row["id"])
                            await cur.execute(f"UPDATE resumes SET {', '.join(updates)} WHERE id = %s;", tuple(params))
                            await conn.commit()
                        data = row["parsed_json"]
                        return data if isinstance(data, dict) else json.loads(data)

        return None

    async def get_history_list(self, limit: int = 30, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch past resume evaluations strictly scoped to the authenticated user."""
        if not user_id:
            # Unauthenticated users receive an empty history list for privacy
            return []

        if not self._is_connected or not self._pool:
            items = []
            for item in reversed(list(self._in_memory_analyses.values())):
                if item.get("user_id") == user_id:
                    items.append({
                        "id": item["id"],
                        "full_name": item["full_name"] or "Candidate",
                        "email": item["email"],
                        "target_role": item.get("target_role") or "Target Role",
                        "target_company": item.get("target_company") or "",
                        "ats_score": item["ats_score"],
                        "created_at": item.get("created_at", "Recent")
                    })
            return items[:limit]

        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute("""
                    SELECT id, full_name, email, target_role, target_company, ats_score, 
                           to_char(created_at, 'Mon DD, YYYY HH24:MI') as created_at
                    FROM resumes
                    WHERE user_id = %s AND parsed_json IS NOT NULL AND parsed_json != '{}'::jsonb
                    ORDER BY created_at DESC
                    LIMIT %s;
                """, (user_id, limit))
                rows = await cur.fetchall()
                items = []
                for r in rows:
                    items.append({
                        "id": r["id"],
                        "full_name": r["full_name"] or "Candidate",
                        "email": r.get("email", ""),
                        "target_role": r.get("target_role") or "Target Role",
                        "target_company": r.get("target_company") or "",
                        "ats_score": float(r.get("ats_score", 0.0)),
                        "created_at": r.get("created_at") or "Recent"
                    })
                return items

    async def get_analysis_by_id(self, resume_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Fetch complete stored analysis payload by ID with user authorization check."""
        if not self._is_connected or not self._pool:
            item = self._in_memory_analyses.get(resume_id)
            if item and (user_id is None or item.get("user_id") == user_id):
                return item.get("parsed_json")
            return None

        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                if user_id:
                    await cur.execute("SELECT parsed_json FROM resumes WHERE id = %s AND user_id = %s;", (resume_id, user_id))
                else:
                    await cur.execute("SELECT parsed_json FROM resumes WHERE id = %s;", (resume_id,))
                r = await cur.fetchone()
                if not r or not r.get("parsed_json"):
                    return None
                data = r["parsed_json"]
                return data if isinstance(data, dict) else json.loads(data)

    async def delete_analysis(self, resume_id: str, user_id: Optional[str] = None) -> bool:
        """Deletes an analysis record strictly if owned by user."""
        if not user_id:
            return False

        self._in_memory_analyses.pop(resume_id, None)
        if not self._is_connected or not self._pool:
            return True

        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM resumes WHERE id = %s AND user_id = %s;", (resume_id, user_id))
                await conn.commit()
                return cur.rowcount > 0

    async def save_chunks(self, resume_id: str, chunks_with_embeddings: List[Dict[str, Any]]):
        """Saves chunk text and pgvector embeddings."""
        if not self._is_connected or not self._pool:
            return

        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    INSERT INTO resumes (id) VALUES (%s) ON CONFLICT (id) DO NOTHING;
                """, (resume_id,))
                await cur.execute("DELETE FROM resume_chunks WHERE resume_id = %s;", (resume_id,))

                for chunk in chunks_with_embeddings:
                    chunk_id = f"{resume_id}-chunk-{chunk['index']}"
                    await cur.execute("""
                        INSERT INTO resume_chunks (id, resume_id, chunk_index, chunk_text, embedding)
                        VALUES (%s, %s, %s, %s, %s);
                    """, (
                        chunk_id,
                        resume_id,
                        chunk["index"],
                        chunk["text"],
                        chunk["embedding"]
                    ))
                await conn.commit()

    async def vector_search(self, query_embedding: List[float], resume_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Vector cosine similarity search using pgvector <=> operator."""
        if not self._is_connected or not self._pool:
            return []

        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute("""
                    SELECT chunk_text, (1 - (embedding <=> %s::vector)) as similarity
                    FROM resume_chunks
                    WHERE resume_id = %s
                    ORDER BY embedding <=> %s::vector ASC
                    LIMIT %s;
                """, (query_embedding, resume_id, query_embedding, limit))
                rows = await cur.fetchall()
                return [dict(r) for r in rows]


db = DatabaseManager()
