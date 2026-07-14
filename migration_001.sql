-- ============================================================================
-- Migration 001 — cohort/bulk add: structured location, DOB-estimate flag, batches.
-- Run ONCE in the Supabase SQL editor (after schema.sql). Safe to re-run.
-- ============================================================================

alter table mice add column if not exists dob_estimated boolean default false; -- DOB was computed from an age
alter table mice add column if not exists room       text;
alter table mice add column if not exists rack       text;
alter table mice add column if not exists rack_row   text;   -- may be a single value or a range like "1-4"
alter table mice add column if not exists rack_col   text;   -- e.g. "A" or "A-C"
alter table mice add column if not exists n_cages    int;    -- # cages the cohort occupies (informational)
alter table mice add column if not exists batch_id   uuid;   -- groups mice added together as one cohort
-- NOTE: `facility` already exists (text) — it now holds CRAF / SAF / EBS / Other.

create index if not exists mice_facility_idx on mice(facility);
create index if not exists mice_batch_idx    on mice(batch_id);

-- Recreate the view so it exposes the new columns (m.* is expanded at CREATE time).
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

-- Facility vocabulary (edit here to add more; the app reads this).
insert into app_config (key, value) values ('facilities', 'CRAF,SAF,EBS,Other')
on conflict (key) do update set value = excluded.value;
