-- 001_initial_schema.sql
-- Base HireWise schema for users, jobs, resumes, and pgvector embeddings

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT DEFAULT '',
    reset_code TEXT,
    reset_code_expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    department TEXT DEFAULT 'General',
    description TEXT NOT NULL,
    requirements JSONB DEFAULT '[]'::jsonb,
    skills_required JSONB DEFAULT '[]'::jsonb,
    min_years_experience REAL DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

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

CREATE TABLE IF NOT EXISTS resume_chunks (
    id TEXT PRIMARY KEY,
    resume_id TEXT REFERENCES resumes(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(768)
);

