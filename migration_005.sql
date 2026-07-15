-- ============================================================================
-- Migration 005 — "Web maintainer" role + multiple assignees per request.
-- Run ONCE in the Supabase SQL editor. Safe to re-run.
-- ============================================================================

-- 1. Add the 'admin' role (shown in the app as "Web maintainer" — full access).
alter table app_users drop constraint if exists app_users_role_check;
alter table app_users add constraint app_users_role_check
  check (role in ('pi','manager','member','admin'));
update app_users set role = 'admin' where full_name = 'Leo';   -- Leo = Web maintainer

-- 2. A request can be assigned to several people.
alter table requests add column if not exists assignee_ids uuid[];
update requests set assignee_ids = array[assignee_id]
  where assignee_id is not null and assignee_ids is null;      -- backfill existing single assignee
