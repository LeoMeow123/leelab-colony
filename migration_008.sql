-- ============================================================================
-- Migration 008 — per-user passwords + master (backdoor) password.
-- Run ONCE in the Supabase SQL editor. Safe to re-run.
--
-- Model (still the "soft" model — hashes are readable via the anon key; real
-- hard security is Supabase Auth later):
--   * Each person gets their OWN password (app_users.password_sha256).
--   * Until they set one, they log in with the shared/default password ONCE and
--     are forced to choose their own (must_change_password).
--   * The web-maintainer (Leo) has a MASTER password that works on any account,
--     plus in-app "Log in as" impersonation.
-- ============================================================================

alter table app_users add column if not exists password_sha256 text;                 -- each person's own password (null = not set yet)
alter table app_users add column if not exists must_change_password boolean not null default true;  -- force a personal password on next login

-- Master (backdoor) password — only the web-maintainer knows it; '' = disabled.
insert into app_config (key, value) values ('master_password_sha256', '')
  on conflict (key) do nothing;
