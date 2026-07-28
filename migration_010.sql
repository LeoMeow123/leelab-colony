-- ============================================================================
-- Migration 010 — first-class breeding cages.
-- A `breeding` mouse is in an active breeding cage: it is grouped by cage (not by
-- sex/age), shown apart, and is NOT requestable. Weaning = set breeding = false.
-- Run ONCE in the Supabase SQL editor. Safe to re-run.
-- ============================================================================

alter table mice add column if not exists breeding boolean not null default false;
create index if not exists mice_breeding_idx on mice(breeding) where breeding;

-- Recreate mouse_v so it exposes the new `breeding` column (m.* is frozen at CREATE).
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
