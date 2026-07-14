-- ============================================================================
-- Migration 002 — allow deleting mice (so a mis-added cohort can be undone),
-- and clean up the end-to-end test rows created while verifying migration 001.
-- Run ONCE in the Supabase SQL editor. Safe to re-run.
-- ============================================================================

-- 1. Delete policy for mice. Until now `mice` was archive-only (status = dead /
--    transferred) with no delete policy, so PostgREST silently deleted 0 rows.
--    This matches the shared-key "everyone can edit" model; the app confirms
--    before deleting and writes a DELETE / DELETE_COHORT row to audit_log.
drop policy if exists mice_del on mice;
create policy mice_del on mice for delete using (true);

-- 2. Remove the verification test rows (2 mice tagged genotype_label = 'TEST-DELETE').
delete from mice where genotype_label = 'TEST-DELETE';
