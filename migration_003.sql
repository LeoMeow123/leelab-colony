-- ============================================================================
-- Migration 003 — experiments-per-mouse + health-oriented status vocabulary.
-- Run ONCE in the Supabase SQL editor. Safe to re-run.
-- ============================================================================

-- 1. Experiments the mouse has been through (comma-separated tags: T-maze, Social, HCM, …).
alter table mice add column if not exists experiments text;

-- 2. Status vocabulary: 'alive' -> 'healthy', add 'diseased'.
--    Drop the old CHECK first so the migrating UPDATE isn't rejected by it.
alter table mice drop constraint if exists mice_status_check;
update mice set status = 'healthy' where status = 'alive';
alter table mice alter column status set default 'healthy';
alter table mice add constraint mice_status_check
  check (status in ('healthy','diseased','sacrificed','dead','transferred','unknown'));

-- 3. Recreate the view so it exposes the new `experiments` column (m.* is frozen at CREATE time).
drop view if exists mouse_v;
create view mouse_v with (security_invoker = true) as
select
  m.*,
  (coalesce(m.date_of_death, current_date) - m.dob)                     as age_days,
  round((coalesce(m.date_of_death, current_date) - m.dob) / 7.0, 1)     as age_weeks,
  round((coalesce(m.date_of_death, current_date) - m.dob) / 30.44, 1)   as age_months,
  (m.last_verified is not null and m.last_verified < current_date - 30) as is_stale,
  a.full_name as owner_name
from mice m
left join app_users a on a.id = m.responsible_person;
grant select on mouse_v to anon, authenticated;
