import asyncio
import hashlib
import logging
import math
import re
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types
import numpy as np

from app.config import get_settings
from app.database import db

logger = logging.getLogger("hirewise.vector")


class VectorService:
    EMBEDDING_DIM = 768

    def __init__(self):
        self._client: Optional[genai.Client] = None
        self._cache: Dict[str, List[float]] = {}
        self._init_client()

    def _init_client(self):
        settings = get_settings()
        if settings.GEMINI_API_KEY:
            try:
                self._client = genai.Client(
                    api_key=settings.GEMINI_API_KEY,
                    http_options=types.HttpOptions(api_version="v1beta")
                )
                logger.info("VectorService initialized with Google GenAI embeddings (v1beta).")
            except Exception as e:
                logger.error(f"Failed to initialize GenAI client for embeddings: {e}")
                self._client = None

    def chunk_text(self, text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
        """
        Splits text into layout-aware and semantic chunks.
        Splits primarily on paragraphs/sections, falling back to sliding window.
        """
        raw_sections = [s.strip() for s in text.split("\n\n") if len(s.strip()) > 30]
        chunks: List[str] = []

        current_chunk = ""
        for sec in raw_sections:
            if len(current_chunk) + len(sec) < chunk_size:
                current_chunk = (current_chunk + "\n" + sec).strip()
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sec

        if current_chunk:
            chunks.append(current_chunk)

        # Fallback if no clean sections were formed
        if not chunks:
            words = text.split()
            for i in range(0, len(words), chunk_size - overlap):
                chunk = " ".join(words[i:i + chunk_size])
                if chunk:
                    chunks.append(chunk)

        return chunks if chunks else [text[:chunk_size]]

    async def get_embedding(self, text: str) -> List[float]:
        """
        Generates 768-dimensional vector embedding using Google gemini-embedding-001 with MRL.
        Cached in memory to eliminate redundant API roundtrips.
        Falls back to deterministic normalized pseudo-embedding if API key is not present.
        """
        if not text:
            return self._generate_deterministic_embedding("empty")

        cache_key = hashlib.md5(text[:2000].encode("utf-8")).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]

        settings = get_settings()
        if self._client and settings.GEMINI_API_KEY:
            try:
                result = await asyncio.to_thread(
                    self._client.models.embed_content,
                    model=settings.EMBEDDING_MODEL,
                    contents=text[:2000],
                    config=types.EmbedContentConfig(
                        output_dimensionality=self.EMBEDDING_DIM
                    )
                )
                if hasattr(result, "embeddings") and result.embeddings:
                    values = result.embeddings[0].values
                    floats = [float(v) for v in values]
                    emb = floats if len(floats) == self.EMBEDDING_DIM else floats[:self.EMBEDDING_DIM]
                    self._cache[cache_key] = emb
                    return emb
                elif hasattr(result, "embedding") and result.embedding:
                    floats = [float(v) for v in result.embedding.values]
                    emb = floats if len(floats) == self.EMBEDDING_DIM else floats[:self.EMBEDDING_DIM]
                    self._cache[cache_key] = emb
                    return emb
            except Exception as e:
                logger.error(f"Google embed_content failed: {e}. Using deterministic fallback embedding.")

        emb = self._generate_deterministic_embedding(text)
        self._cache[cache_key] = emb
        return emb

    def _generate_deterministic_embedding(self, text: str) -> List[float]:
        """
        Generates a deterministic, unit-normalized 768-dimensional float vector
        using SHA-256 seed for reproducible vector mathematics.
        """
        # Create seed from text content
        hasher = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(hasher[:4], "big")
        rng = np.random.RandomState(seed)
        
        # Generate random normal vector
        vector = rng.randn(self.EMBEDDING_DIM)
        # Normalize to unit length
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return [float(v) for v in vector]

    def cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Computes cosine similarity between two float vectors (0.0 to 1.0)."""
        a = np.array(vec_a, dtype=float)
        b = np.array(vec_b, dtype=float)
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        sim = float(dot / (norm_a * norm_b))
        # Clamp to [0, 1] range for ATS scoring
        return max(0.0, min(1.0, (sim + 1.0) / 2.0 if sim < 0 else sim))

    async def hybrid_search_and_score(
        self,
        resume_id: str,
        resume_chunks: List[str],
        job_description_text: str,
        job_skills: List[str]
    ) -> Dict[str, Any]:
        """
        Advanced Hybrid RAG Retrieval:
        1. Embeds job description (cached).
        2. Embeds all resume chunks concurrently in parallel via asyncio.gather (~1s).
        3. Performs dense vector cosine similarity (via pgvector <=> or in-memory).
        4. Performs sparse keyword / full-text matching for required skills.
        5. Custom re-ranking node: hybrid_score = 0.65 * dense_sim + 0.35 * sparse_match.
        """
        # 1. Embed job description (cached if seen before)
        job_embedding = await self.get_embedding(job_description_text)

        # 2. Embed all chunks concurrently in parallel using asyncio.gather (~1s total)
        chunk_embeddings = await asyncio.gather(*[self.get_embedding(chunk) for chunk in resume_chunks])

        chunk_records = []
        for idx, (chunk, chunk_emb) in enumerate(zip(resume_chunks, chunk_embeddings)):
            chunk_records.append({
                "index": idx,
                "text": chunk,
                "embedding": chunk_emb
            })

        if db.is_connected:
            try:
                await db.save_chunks(resume_id, chunk_records)
            except Exception as e:
                logger.error(f"Error saving chunks to pgvector: {e}")

        # 3. Dense Vector Retrieval (pgvector <=> or in-memory)
        pg_results = []
        if db.is_connected:
            try:
                pg_results = await db.vector_search(job_embedding, resume_id=resume_id, limit=5)
            except Exception as e:
                logger.error(f"pgvector search error: {e}")

        if pg_results:
            similarities = [max(0.0, float(r.get("similarity", 0.5))) for r in pg_results]
            avg_vector_sim = float(np.mean(similarities)) if similarities else 0.5
        else:
            # In-memory cosine calculation across chunks
            sims = [self.cosine_similarity(job_embedding, item["embedding"]) for item in chunk_records]
            avg_vector_sim = float(np.mean(sims)) if sims else 0.5

        # 4. Sparse Keyword / Skill Matching
        full_resume_text = " ".join(resume_chunks).lower()
        matched_skills = []
        missing_skills = []

        for skill in job_skills:
            pattern = rf"\b{re.escape(skill.lower())}\b"
            if re.search(pattern, full_resume_text):
                matched_skills.append(skill)
            else:
                missing_skills.append(skill)

        total_req_skills = len(job_skills)
        skill_match_ratio = (len(matched_skills) / total_req_skills) if total_req_skills > 0 else 0.7

        # 5. Hybrid Re-Ranking Calculation
        # Vector score contributes 65%, exact keyword/skill overlap contributes 35%
        hybrid_semantic_score = (0.65 * avg_vector_sim) + (0.35 * skill_match_ratio)

        return {
            "avg_vector_similarity": avg_vector_sim,
            "skill_match_ratio": skill_match_ratio,
            "hybrid_semantic_score": hybrid_semantic_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "chunk_count": len(resume_chunks)
        }


vector_service = VectorService()

