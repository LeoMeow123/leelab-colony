-- ============================================================================
-- Migration 006 — richer requests: task type + which-mice/location.
-- Run ONCE in the Supabase SQL editor. Safe to re-run.
-- (Status lifecycle uses the existing vocab: open → fulfilled [= "Done"] → closed;
--  plus denied / cancelled. No status change needed.)
-- ============================================================================

alter table requests add column if not exists request_type text;  -- Genotype / Ear-tag / Move / Provide mice / Breed / Other
alter table requests add column if not exists mice_info text;      -- which mice + where (tags, cage, room) so the assignee can act
