-- Migration: fix skills.embedding column from vector(768) to vector(384)
-- The SBERT model paraphrase-multilingual-MiniLM-L12-v2 outputs 384-dim vectors.
-- Run this once against your existing database, then re-run add_embeddings.py.

-- Drop the IVFFlat index first (it depends on the column type)
DROP INDEX IF EXISTS idx_skills_embedding;

-- Clear embeddings that were never successfully stored (NULLs stay NULL)
-- and change the column dimension to 384
ALTER TABLE skills
    ALTER COLUMN embedding TYPE vector(384)
    USING NULL;  -- reset existing values so wrong-dim data doesn't block the ALTER

-- Recreate the index with correct dimension
CREATE INDEX IF NOT EXISTS idx_skills_embedding
    ON skills USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
