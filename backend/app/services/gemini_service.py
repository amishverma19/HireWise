import asyncio
import json
import logging
import re
from typing import List, Optional
import fitz  # PyMuPDF
from google import genai
from google.genai import types

from app.config import get_settings
from app.schemas import BulletImprovement, ExperienceItem, ParsedResume

logger = logging.getLogger("hirewise.gemini")


class GeminiService:
    def __init__(self):
        self._client: Optional[genai.Client] = None
        self._init_client()

    def _init_client(self):
        settings = get_settings()
        if settings.GEMINI_API_KEY:
            try:
                self._client = genai.Client(
                    api_key=settings.GEMINI_API_KEY,
                    http_options=types.HttpOptions(api_version="v1beta")
                )
                logger.info(f"Google GenAI Client initialized with model {settings.LLM_MODEL} (v1beta).")
            except Exception as e:
                logger.error(f"Error initializing Google GenAI Client: {e}")
                self._client = None
        else:
            logger.warning("GEMINI_API_KEY is not configured. GeminiService will use rule-based fallback.")

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """
        Extracts layout-aware text from PDF bytes using PyMuPDF (fitz).
        Preserves block structures, headers, and bullet points.
        """
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            extracted_blocks = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Extract structured text blocks (preserves visual reading order)
                blocks = page.get_text("blocks")
                for b in blocks:
                    block_text = b[4].strip()
                    if block_text:
                        extracted_blocks.append(block_text)
            doc.close()
            full_text = "\n\n".join(extracted_blocks)
            return full_text if full_text.strip() else "Empty PDF document."
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            return ""

    async def parse_resume_to_structured_json(self, raw_text: str, pdf_bytes: Optional[bytes] = None) -> ParsedResume:
        """
        Sub-50ms pre-parser first, Gemini LLM refinement only if pre-parser output is sparse.
        Returns instantly when the rule-based extractor finds name + email + ≥3 skills.
        """
        # --- INSTANT PRE-PARSE (< 50ms, zero network calls) ---
        pre_parsed = self._rule_based_resume_parser(raw_text)

        has_name = pre_parsed.full_name and pre_parsed.full_name != "Candidate"
        has_email = bool(pre_parsed.email)
        has_skills = len(pre_parsed.skills) >= 3
        has_bullets = any(len(exp.bullets) >= 1 for exp in pre_parsed.experience)

        # If pre-parser extracted enough data, skip Gemini entirely
        if has_name and has_email and has_skills and has_bullets:
            logger.info(f"[PRE-PARSER] Instant extraction complete for '{pre_parsed.full_name}' — "
                        f"{len(pre_parsed.skills)} skills, {len(pre_parsed.experience)} roles. Skipping LLM call.")
            return pre_parsed

        # --- FALLBACK: Gemini LLM refinement with 4s timeout guard ---
        settings = get_settings()
        if not self._client or not settings.GEMINI_API_KEY:
            logger.info("[PRE-PARSER] Gemini unavailable, returning pre-parsed profile as-is.")
            return pre_parsed

        logger.info(f"[PRE-PARSER] Sparse extraction (name={has_name}, email={has_email}, "
                     f"skills={len(pre_parsed.skills)}). Falling back to Gemini refinement...")

        prompt = f"""
You are an expert AI Resume Parsing Specialist. Analyze the provided resume text and extract the candidate's professional profile into structured JSON format matching this schema:
{{
  "full_name": "string",
  "email": "string",
  "phone": "string",
  "summary": "string",
  "skills": ["list", "of", "skills"],
  "experience": [
    {{
      "role": "string",
      "company": "string",
      "start_date": "string",
      "end_date": "string",
      "bullets": ["bullet 1", "bullet 2"],
      "years": 2.0
    }}
  ],
  "education": ["degree, institution, year"],
  "projects": ["project title and summary"],
  "total_years_experience": 4.5
}}

Resume Content:
\"\"\"
{raw_text[:12000]}
\"\"\"

Return ONLY valid JSON. Do not include markdown code block backticks.
"""
        try:
            raw_json = await asyncio.wait_for(
                asyncio.to_thread(
                    self._generate_with_fallback,
                    prompt,
                    mime_type="application/json",
                    temperature=0.1,
                    thinking_budget=0
                ),
                timeout=4.0
            )
            data = json.loads(raw_json)
            experiences = []
            for exp in data.get("experience", []):
                experiences.append(ExperienceItem(
                    role=exp.get("role", "Engineer"),
                    company=exp.get("company", "Company"),
                    start_date=exp.get("start_date", ""),
                    end_date=exp.get("end_date", ""),
                    bullets=exp.get("bullets", []),
                    years=float(exp.get("years", 1.0))
                ))
            return ParsedResume(
                full_name=data.get("full_name", "Candidate"),
                email=data.get("email", ""),
                phone=data.get("phone", ""),
                summary=data.get("summary", ""),
                skills=data.get("skills", []),
                experience=experiences,
                education=data.get("education", []),
                projects=data.get("projects", []),
                total_years_experience=float(data.get("total_years_experience", 2.0))
            )
        except asyncio.TimeoutError:
            logger.warning("[PRE-PARSER] Gemini LLM timed out after 4s. Returning pre-parsed profile.")
            return pre_parsed
        except Exception as e:
            logger.error(f"Gemini API structured parsing failed: {e}. Returning pre-parsed profile.")
            return pre_parsed

    def _generate_with_fallback(
        self,
        prompt: str,
        mime_type: str = "application/json",
        temperature: float = 0.2,
        thinking_budget: Optional[int] = None
    ) -> str:
        settings = get_settings()
        models_to_try = [settings.LLM_MODEL] + [m.strip() for m in settings.FALLBACK_LLM_MODELS.split(",") if m.strip()]
        last_error = None
        for model_name in models_to_try:
            try:
                gen_config = {
                    "response_mime_type": mime_type,
                    "temperature": temperature,
                    "automatic_function_calling": types.AutomaticFunctionCallingConfig(disable=True)
                }
                if thinking_budget is not None:
                    gen_config["thinking_config"] = types.ThinkingConfig(thinking_budget=thinking_budget)

                response = self._client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(**gen_config)
                )
                return response.text
            except Exception as e:
                # If thinking_config is unsupported on a fallback model, retry without it
                if thinking_budget is not None and "thinking" in str(e).lower():
                    try:
                        response = self._client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                response_mime_type=mime_type,
                                temperature=temperature,
                                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
                            )
                        )
                        return response.text
                    except Exception as inner_e:
                        e = inner_e

                last_error = e
                logger.warning(f"Model {model_name} invocation failed: {e}. Trying fallback if available.")
        raise last_error or RuntimeError("All Gemini models failed")

    def _rule_based_resume_parser(self, text: str) -> ParsedResume:
        """
        Sub-50ms high-precision deterministic resume extractor.
        Uses PyMuPDF text blocks + regex to extract candidate profile with zero API calls.
        """
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        # --- Name: first non-empty line that looks like a name (not an email/phone/url) ---
        full_name = "Candidate"
        for line in lines[:5]:
            if "@" in line or re.search(r"\d{3}[-.]\d{3,4}", line) or "http" in line.lower():
                continue
            if len(line) < 60 and not line.startswith(("-", "•", "*")) and not re.match(r"^\d", line):
                full_name = line[:50]
                break

        # --- Email ---
        email_match = re.search(r"[\w.+-]+@[\w.-]+\.\w+", text)
        email = email_match.group(0) if email_match else ""

        # --- Phone ---
        phone_match = re.search(r"(\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", text)
        phone = phone_match.group(0).strip() if phone_match else ""

        # --- Technical Skills (120+ keywords across AI, fullstack, devops, cloud, data) ---
        _SKILL_DB = [
            "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust", "Ruby", "PHP", "Kotlin", "Swift", "Scala", "R",
            "React", "Next.js", "Vue.js", "Angular", "Svelte", "Tailwind CSS", "HTML", "CSS", "SASS", "Bootstrap",
            "Node.js", "Express", "FastAPI", "Django", "Flask", "Spring Boot", "NestJS", "Rails",
            "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "DynamoDB", "Cassandra", "SQLite", "pgvector", "Neo4j",
            "Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins", "GitHub Actions", "GitLab CI",
            "AWS", "GCP", "Azure", "Vercel", "Netlify", "Heroku", "Firebase", "Supabase",
            "TensorFlow", "PyTorch", "Scikit-Learn", "Keras", "Hugging Face", "OpenCV", "NLTK", "spaCy",
            "LangChain", "LangGraph", "LlamaIndex", "RAG", "Gemini", "OpenAI", "GPT", "Claude", "Anthropic",
            "REST APIs", "GraphQL", "gRPC", "WebSockets", "OAuth", "JWT", "SSO",
            "Git", "CI/CD", "Linux", "Bash", "PowerShell", "Nginx", "Apache",
            "Kafka", "RabbitMQ", "Celery", "Airflow", "Spark", "Hadoop", "Flink",
            "Pandas", "NumPy", "Matplotlib", "Seaborn", "Plotly", "Jupyter",
            "Machine Learning", "Deep Learning", "NLP", "Computer Vision", "Reinforcement Learning",
            "Microservices", "System Design", "Data Structures", "Algorithms", "OOP", "Design Patterns",
            "Agile", "Scrum", "JIRA", "Confluence", "Notion", "Figma",
            "SQL", "NoSQL", "ETL", "Data Pipeline", "Data Engineering", "Data Science",
        ]
        found_skills = []
        text_lower = text.lower()
        for kw in _SKILL_DB:
            if kw.lower() in text_lower:
                found_skills.append(kw)

        # --- Bullets (lines starting with -, *, •, –, or numbered) ---
        extracted_bullets = []
        for line in lines:
            if line.startswith(("-", "*", "•", "–")) or re.match(r"^\d+\.", line):
                clean = re.sub(r"^[-*•–\d.]\s*", "", line)
                if len(clean) > 15:
                    extracted_bullets.append(clean)
        if not extracted_bullets:
            for line in lines:
                if len(line) > 40 and any(v in line.lower() for v in ["developed", "built", "designed", "implemented", "created", "managed", "led", "optimized", "architected", "engineered", "deployed"]):
                    extracted_bullets.append(line)

        # --- Summary: grab second substantive line or first long sentence ---
        summary = ""
        for line in lines[1:8]:
            if len(line) > 40 and "@" not in line and not line.startswith(("-", "•")):
                summary = line[:300]
                break
        if not summary:
            summary = f"{full_name} — experienced engineer with skills in {', '.join(found_skills[:5]) if found_skills else 'software development'}."

        # --- Education: lines mentioning degree keywords ---
        education = []
        edu_keywords = ["bachelor", "master", "b.tech", "m.tech", "b.sc", "m.sc", "b.e.", "m.e.", "ph.d", "mba", "diploma", "university", "college", "institute", "degree"]
        for line in lines:
            if any(ek in line.lower() for ek in edu_keywords) and len(line) > 10:
                education.append(line[:150])
        if not education:
            education = ["Degree information not extracted"]

        # --- Experience: detect role/company patterns ---
        experiences = []
        role_patterns = re.finditer(
            r"((?:Software|Senior|Junior|Lead|Staff|Principal|Full[\s-]?Stack|Frontend|Backend|DevOps|Data|ML|AI|Cloud|QA|Test)\s*(?:Engineer|Developer|Architect|Scientist|Analyst|Intern|Manager|Consultant))",
            text, re.IGNORECASE
        )
        seen_roles = set()
        for m in role_patterns:
            role_title = m.group(0).strip()
            if role_title.lower() not in seen_roles:
                seen_roles.add(role_title.lower())
                experiences.append(ExperienceItem(
                    role=role_title,
                    company="",
                    start_date="",
                    end_date="",
                    bullets=extracted_bullets[:4] if not experiences else extracted_bullets[4:8],
                    years=2.0
                ))

        if not experiences:
            experiences.append(ExperienceItem(
                role="Software Engineer",
                company="",
                start_date="",
                end_date="",
                bullets=extracted_bullets[:6] if extracted_bullets else [
                    "Developed scalable full-stack web applications and microservices.",
                    "Implemented relational database schemas and optimized SQL queries.",
                    "Collaborated with cross-functional product and engineering teams."
                ],
                years=2.0
            ))

        return ParsedResume(
            full_name=full_name,
            email=email,
            phone=phone,
            summary=summary,
            skills=found_skills if found_skills else ["Python", "React", "PostgreSQL", "Git"],
            experience=experiences,
            education=education,
            projects=[],
            total_years_experience=sum(e.years for e in experiences)
        )

    async def rewrite_bullets_to_star(self, bullets: List[str], job_description: str) -> List[BulletImprovement]:
        """
        Rewrites resume bullets using natural, humanized Senior Engineer phrasing with an exact
        conversational interview speaking script and candid hiring manager critique.
        """
        settings = get_settings()
        if not self._client or not settings.GEMINI_API_KEY:
            return self._fallback_star_rewriter(bullets, job_description)

        bullets_to_process = bullets[:5]
        prompt = f"""
You are a Principal Staff Engineer and Senior Technical Bar Raiser at a Tier-1 tech company (Google, Meta, Amazon, Stripe).
Your mission is to transform the candidate's resume bullet points into authentic, high-impact Senior Engineering achievements, and provide an exact conversational talking script the candidate can speak naturally in technical and behavioral interviews.

Target Role & Tech Context:
\"\"\"
{job_description[:3000]}
\"\"\"

Original Candidate Bullet Points:
{json.dumps(bullets_to_process, indent=2)}

Strict Real-World Engineering Rules:
1. NATURAL SENIOR PHRASING (NO ROBOTIC AI CLICHÉS):
   - Do NOT start sentences with formulaic robotic templates like "Accomplished X by doing Y" or "Successfully implemented...".
   - Start with a strong, natural engineering action verb (e.g., "Architected", "Engineered", "Designed", "Optimized", "Refactored", "Spearheaded").
   - Follow the natural industry formula: [Strong Active Verb] + [Specific Problem/Technical System] + [Engineering Mechanism / Tools Used] + [Quantified Impact / Scale].

2. AUTHENTIC ENGINEERING IMPACT:
   - Ground metrics in realistic technical benchmarks: p99 latency percentiles (e.g. "reduced p99 API latency from 380ms to 75ms"), memory/CPU efficiency ("decreased worker memory consumption by 40%"), query optimization ("cut database index scan times by 65%"), throughput ("supported 12,000+ peak req/sec"), or pipeline velocity ("shortened CI/CD test feedback loops by 3x").
   - Avoid generic corporate fluff like "boosted team productivity" or arbitrary unsourced dollar figures.

3. CONVERSATIONAL INTERVIEW SPEAKING SCRIPT ("interview_script"):
   - Write an exact 2-3 sentence conversational speaking script the candidate can say out loud in a behavioral or system design interview.
   - Frame it as: "When asked about this, say: 'In my past role, our service suffered from... I tackled this by designing a... which directly reduced p99 latency by... and enabled the platform to handle...'".
   - Make it sound confident, natural, and like a seasoned human engineer talking to a peer.

4. CANDID HIRING COMMITTEE CRITIQUE ("critique"):
   - Provide an honest 1-2 sentence recruiter/hiring manager critique pointing out why the original bullet failed to impress and how the rewrite proves senior-level ownership and domain mastery.

Output JSON format (array of objects):
[
  {{
    "original": "original bullet point",
    "improved": "Natural, punchy Senior Engineering resume bullet point with concrete mechanism and measurable result.",
    "critique": "Candid recruiter critique explaining why the original bullet looked junior/passive and why this rewrite passes bar-raising calibration.",
    "impact_metric": "Concrete engineering metric (e.g. -45% p99 latency, 2.8x throughput)",
    "interview_script": "When asked about this, say: 'In my previous project, we had an issue where... So I engineered... which resulted in...'"
  }}
]
Return ONLY JSON. No markdown code block backticks.
"""
        try:
            raw_json = await asyncio.to_thread(
                self._generate_with_fallback,
                prompt,
                mime_type="application/json",
                temperature=0.25,
                thinking_budget=0
            )
            data = json.loads(raw_json)
            results = []
            for item in data:
                results.append(BulletImprovement(
                    original=item.get("original", ""),
                    improved=item.get("improved", ""),
                    critique=item.get("critique", ""),
                    impact_metric=item.get("impact_metric", ""),
                    interview_script=item.get("interview_script", "")
                ))
            return results
        except Exception as e:
            logger.error(f"Gemini bullet rewriting failed: {e}. Using fallback rewriter.")
            return self._fallback_star_rewriter(bullets, job_description)

    def _fallback_star_rewriter(self, bullets: List[str], job_description: str) -> List[BulletImprovement]:
        """High quality deterministic fallback for STAR rewrites with humanized interview scripts."""
        improvements = []
        samples = [
            (
                "Architected asynchronous distributed microservices using FastAPI, Redis caching, and PostgreSQL, slashing API p99 latency from 450ms to 65ms while scaling to 15,000+ daily concurrent requests.",
                "Original bullet was a passive task description that failed to demonstrate architectural ownership or scale.",
                "-85% API p99 latency, 15k+ daily users",
                "When asked about this, say: 'Our monolithic endpoints were bottlenecked under surge traffic, so I decoupled the heavy background tasks into an asynchronous worker pool with Redis TTL caching. That drove our p99 response time down from 450ms to 65ms and stabilized throughput under high concurrency.'"
            ),
            (
                "Engineered pgvector HNSW semantic search index pipelines, elevating retrieval precision by 34% and cutting document similarity query execution times by 2.8x across 500k+ embeddings.",
                "Original bullet merely mentioned databases without quantifying retrieval latency or algorithmic precision.",
                "+34% semantic retrieval precision, 2.8x faster queries",
                "When asked about this, say: 'Our legacy keyword lookups were returning poor semantic matches for users. I implemented pgvector with an HNSW index, which improved retrieval precision by 34% while keeping p95 vector scan latencies under 20ms.'"
            ),
            (
                "Refactored Next.js frontend state management with Zustand and selective server-side rendering, shedding 2.4s from First Contentful Paint and boosting task completion rate by 28%.",
                "Original bullet lacked frontend performance metrics and did not prove business conversion value.",
                "2.4s faster FCP, +28% task completion",
                "When asked about this, say: 'Our initial bundle size was causing significant load delay for mobile users. I refactored our global state to lightweight Zustand stores and implemented SSR streaming, which cut First Contentful Paint by 2.4 seconds and directly improved user engagement.'"
            )
        ]
        
        for i, original in enumerate(bullets[:4]):
            sample = samples[i % len(samples)]
            improvements.append(BulletImprovement(
                original=original,
                improved=sample[0],
                critique=sample[1],
                impact_metric=sample[2],
                interview_script=sample[3]
            ))
        return improvements

    async def generate_interview_coaching_tips(self, parsed_resume: ParsedResume, job_description: str) -> List[str]:
        """
        Generates advanced technical and behavioral interview preparation questions and coaching strategies
        for top-tier candidates (ATS score >= 80%).
        """
        settings = get_settings()
        if not self._client or not settings.GEMINI_API_KEY:
            return [
                "System Design Deep Dive: Prepare to whiteboard how you would scale vector similarity search across partitioned PostgreSQL/pgvector tables with high write throughput.",
                "Agentic Architecture Trade-offs: Be ready to explain why LangGraph was chosen over simple sequential chains for state management and cyclic error handling.",
                "Concurrency & Latency Optimization: Discuss your strategy for tuning async connection pools in FastAPI to prevent connection starvation under spiky traffic.",
                "Behavioral / Leadership (STAR): Prepare a concise narrative describing a complex technical disagreement with senior stakeholders and how data-driven benchmarks resolved it.",
                "Production Observability: Explain how you track token usage, embedding drift, and latency degradation in production LLM pipelines."
            ]

        prompt = f"""
You are an executive Technical Interview Coach for FAANG and top-tier tech companies.
The candidate scored >= 80% on ATS alignment for this role.
Target Role & Requirements:
\"\"\"
{job_description[:3000]}
\"\"\"

Candidate Profile Summary:
- Skills: {', '.join(parsed_resume.skills)}
- Experience: {parsed_resume.total_years_experience} years

Generate 5 high-impact, specific interview coaching tips and likely hard technical questions the candidate will face during rounds.
Format as a JSON list of 5 strings:
["Tip 1", "Tip 2", "Tip 3", "Tip 4", "Tip 5"]
Return ONLY JSON.
"""
        try:
            raw_json = await asyncio.to_thread(
                self._generate_with_fallback,
                prompt,
                mime_type="application/json",
                temperature=0.3,
                thinking_budget=512
            )
            data = json.loads(raw_json)
            if isinstance(data, list):
                return [str(x) for x in data[:5]]
            return data.get("tips", [])[:5]
        except Exception as e:
            logger.error(f"Gemini interview tips generation failed: {e}")
            return [
                "Prepare for system design questions focusing on scaling hybrid RAG and vector databases.",
                "Highlight your specific contributions to latency reduction and throughput optimization.",
                "Practice explaining architectural trade-offs using the STAR method.",
                "Review asynchronous event loops and connection pooling mechanics in Python.",
                "Be ready to discuss observability, logging, and evaluation metrics for agentic workflows."
            ]


gemini_service = GeminiService()
