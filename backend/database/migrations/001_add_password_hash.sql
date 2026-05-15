-- Migration 001: add password_hash column to students
-- Run once: psql -U masar_user -d masar -f 001_add_password_hash.sql

ALTER TABLE students
  ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
