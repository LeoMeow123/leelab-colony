-- ============================================================================
-- Migration 004 — per-mouse cage number.
-- Run ONCE in the Supabase SQL editor. Safe to re-run.
-- ============================================================================

alter table mice add column if not exists cage text;   -- cage number/label within a rack (defaults 1,2,3… per cohort; editable)
create index if not exists mice_cage_idx on mice(cage);

-- Recreate the view so it exposes `cage` (m.* is frozen at CREATE time).
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
