-- 002_add_cache_and_interview_scripts.sql
-- Non-destructive migration for fast SHA-256 caching and metadata indexing

ALTER TABLE resumes ADD COLUMN IF NOT EXISTS target_role TEXT DEFAULT '';
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS target_company TEXT DEFAULT '';
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS user_id TEXT REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS file_hash TEXT DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);
CREATE INDEX IF NOT EXISTS idx_resumes_file_hash ON resumes(file_hash);
CREATE INDEX IF NOT EXISTS idx_resumes_hash_role ON resumes(file_hash, target_role);
CREATE INDEX IF NOT EXISTS idx_resumes_email_role ON resumes(email, target_role);

