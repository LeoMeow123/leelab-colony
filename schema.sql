-- ============================================================================
-- Kuo-Fen Lee Lab Mouse Colony DB — schema (Phase 1 core + forward-compatible)
-- Run ONCE in the SQL editor of a NEW Supabase project (Database → SQL editor).
-- Supabase is Postgres 15+, so gen_random_uuid() and security_invoker views work.
-- ============================================================================

-- ---------- reference / people ----------
create table if not exists app_users (
  id uuid primary key default gen_random_uuid(),
  full_name text not null,
  email text,
  role text not null default 'member' check (role in ('pi','manager','member','admin')), -- admin = "Web maintainer" (full access) in the UI
  is_active boolean not null default true,
  password_sha256 text,                              -- each person's own login password (null = not set → onboard with the default once)
  must_change_password boolean not null default true, -- force a personal password on next login
  created_at timestamptz default now()
);

create table if not exists app_config (
  key text primary key,
  value text
);

create table if not exists alleles (
  id uuid primary key default gen_random_uuid(),
  symbol text unique not null,
  gene text,
  display_order int default 0
);

-- ---------- the hub ----------
create table if not exists mice (
  id uuid primary key default gen_random_uuid(),  -- the ONLY global key (print on cage card)
  tag_id text,                     -- ear-tag / cage-card number (NON-unique metadata)
  facility text,
  sex text check (sex in ('M','F','U')),
  dob date,                        -- age is DERIVED from this, never stored
  dob_estimated boolean default false, -- true = dob was back-computed from a rough age
  date_of_death date,
  cohort text,                     -- shown in the UI as "Genotype": controlled vocab WT/APP/Tau/PD/…
  genotype_label text,             -- shown in the UI as "Strain": free text, e.g. C57BL/6, hMAP
  strain_background text,           -- legacy/unused (the UI "Strain" field maps to genotype_label)
  room text,                       -- structured location (also flattened into current_location)
  rack text,
  rack_row text,                   -- single value or a range like "1-4" (legacy; superseded by cage)
  rack_col text,                   -- e.g. "A" or "A-C" (legacy)
  cage text,                       -- cage number/label within a rack (defaults 1,2,3… per cohort; editable)
  n_cages int,                     -- # cages the cohort occupies (informational)
  batch_id uuid,                   -- groups mice added together as one cohort
  status text not null default 'healthy'
    check (status in ('healthy','diseased','sacrificed','dead','transferred','collected','unknown')),
  responsible_person uuid references app_users(id),
  current_location text,
  experiments text,                -- comma-separated experiment tags (T-maze, Social, HCM, …)
  last_verified date,
  notes text,
  created_by uuid references app_users(id),
  updated_by uuid references app_users(id),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index if not exists mice_status_idx   on mice(status);
create index if not exists mice_cohort_idx   on mice(cohort);
create index if not exists mice_owner_idx    on mice(responsible_person);
create index if not exists mice_dob_idx      on mice(dob);
create index if not exists mice_tag_idx      on mice(tag_id);
create index if not exists mice_facility_idx on mice(facility);
create index if not exists mice_batch_idx    on mice(batch_id);
create index if not exists mice_cage_idx     on mice(cage);

create table if not exists mouse_allele (
  mouse_id uuid references mice(id) on delete cascade,
  allele_id uuid references alleles(id),
  zygosity text check (zygosity in ('hom','het','hemi','wt','tg','unknown')),
  primary key (mouse_id, allele_id)
);

-- ---------- experiments / procedures ----------
create table if not exists experiments (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  type text,                       -- hcm/behavior/treatment/histology/breeding
  cohort_label text,
  protocol_number text,
  collaborator text,
  start_date date,
  end_date date,
  status text default 'active',
  responsible_person uuid references app_users(id),
  notes text,
  created_at timestamptz default now()
);

create table if not exists experiment_mice (
  id uuid primary key default gen_random_uuid(),
  experiment_id uuid references experiments(id) on delete cascade,
  mouse_id uuid references mice(id) on delete cascade,
  role text,                       -- subject/control/breeder
  cohort text,
  enrolled_date date,
  exited_date date,
  outcome text,                    -- completed/euthanized/removed/ongoing
  created_by uuid references app_users(id),
  unique (experiment_id, mouse_id)
);

create table if not exists procedures (
  id uuid primary key default gen_random_uuid(),
  mouse_id uuid references mice(id) on delete cascade,
  experiment_id uuid references experiments(id),
  date date not null,
  kind text,                       -- injection/surgery/behavior/weight/genotyping/euthanasia
  agent text,
  dose text,
  performer uuid references app_users(id),
  notes text,
  created_at timestamptz default now()
);

-- ---------- request queue (Phase 2 tables, created now) ----------
create table if not exists requests (
  id uuid primary key default gen_random_uuid(),
  requester_id uuid references app_users(id),
  subject text not null,
  request_type text,               -- Genotype / Ear-tag / Move / Provide mice / Breed / Other
  mice_info text,                  -- which mice + where (tags, cage, room)
  body text,
  needed_sex text,
  needed_cohort text,
  needed_age_min_weeks int,
  needed_age_max_weeks int,
  quantity int,
  target_mouse_id uuid references mice(id),
  assignee_id uuid references app_users(id),   -- primary assignee (kept for compatibility)
  assignee_ids uuid[],                          -- all assignees (a request can go to several people)
  status text not null default 'open'
    check (status in ('open','approved','denied','routed_to_breeding','fulfilled','closed','cancelled')),
  priority int default 0,
  due_by date,
  decision_note text,
  created_at timestamptz default now(),
  decided_at timestamptz
);

create table if not exists request_comments (
  id uuid primary key default gen_random_uuid(),
  request_id uuid references requests(id) on delete cascade,
  author_id uuid references app_users(id),
  body text,
  created_at timestamptz default now()
);

-- ---------- Guardian Angels (lab members' pets) ----------
create table if not exists guardian_angels (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  species text,
  owner_id uuid references app_users(id),
  owner_name text,
  message text,
  photo text,                  -- data-URL (base64 JPEG, resized client-side; no Storage bucket needed)
  created_by uuid references app_users(id),
  created_at timestamptz default now()
);

-- ---------- import staging + audit ----------
create table if not exists raw_import (
  id uuid primary key default gen_random_uuid(),
  source_file text, sheet text, row_num int,
  raw jsonb, extracted jsonb,
  needs_review boolean default true, confidence real,
  dupe_of uuid references mice(id),
  mapped_mouse_id uuid references mice(id),
  reviewed_by uuid references app_users(id),
  created_at timestamptz default now()
);

create table if not exists audit_log (
  id bigserial primary key,
  table_name text, row_id uuid, action text,
  actor_id uuid, changed_at timestamptz default now(),
  old_row jsonb, new_row jsonb
);

-- ============================================================================
-- View: mouse_v — age derived from dob, staleness flag, owner name.
-- security_invoker so the caller's RLS on `mice` applies to the view.
-- ============================================================================
-- drop+create (not "create or replace") because the view uses m.* — replace
-- can't handle a base-table column change on a later re-run.
drop view if exists mouse_v;
create view mouse_v with (security_invoker = true) as
select
  m.*,
  (coalesce(m.date_of_death, current_date) - m.dob)                     as age_days,
  round((coalesce(m.date_of_death, current_date) - m.dob) / 7.0, 1)     as age_weeks,
  round((coalesce(m.date_of_death, current_date) - m.dob) / 30.44, 1)   as age_months,
  (m.last_verified is not null and m.last_verified < current_date - 30) as is_stale,
  a.full_name as owner_name       -- NOTE: invoker-scoped; if you later restrict
                                  -- app_users SELECT, owner_name goes null for hidden rows
from mice m
left join app_users a on a.id = m.responsible_person;

-- ============================================================================
-- Grants + RLS.
-- Internal model: everyone shares the publishable (anon) key; read is open,
-- writes are allowed and attributed in-app + audit_log. Tighten to per-user
-- Supabase Auth later WITHOUT schema changes (just swap the policies).
-- ============================================================================
grant usage on schema public to anon, authenticated;
grant select, insert, update, delete on all tables in schema public to anon, authenticated;
grant select on mouse_v to anon, authenticated;
grant usage, select on all sequences in schema public to anon, authenticated;
-- future-proof: tables/sequences created later auto-get grants (avoids "new table 404")
alter default privileges in schema public grant select, insert, update, delete on tables to anon, authenticated;
alter default privileges in schema public grant usage, select on sequences to anon, authenticated;
-- keep audit_log append-only at the grant level too (RLS also enforces this)
revoke update, delete on audit_log from anon, authenticated;

do $$
declare
  t text;
  all_tbls  text[] := array['app_users','app_config','alleles','mice','mouse_allele',
    'experiments','experiment_mice','procedures','requests','request_comments','raw_import','audit_log','guardian_angels'];
  upd_tbls  text[] := array['app_users','app_config','alleles','mice','mouse_allele',
    'experiments','experiment_mice','procedures','requests','request_comments','raw_import','guardian_angels'];
  del_tbls  text[] := array['mice','mouse_allele','experiment_mice','procedures','request_comments',
    'requests','raw_import','alleles','experiments','guardian_angels'];
begin
  foreach t in array all_tbls loop
    execute format('alter table %I enable row level security;', t);
    execute format('drop policy if exists %I on %I;', t||'_sel', t);
    execute format('create policy %I on %I for select using (true);', t||'_sel', t);
    execute format('drop policy if exists %I on %I;', t||'_ins', t);
    execute format('create policy %I on %I for insert with check (true);', t||'_ins', t);
  end loop;
  foreach t in array upd_tbls loop
    execute format('drop policy if exists %I on %I;', t||'_upd', t);
    execute format('create policy %I on %I for update using (true) with check (true);', t||'_upd', t);
  end loop;
  foreach t in array del_tbls loop
    execute format('drop policy if exists %I on %I;', t||'_del', t);
    execute format('create policy %I on %I for delete using (true);', t||'_del', t);
  end loop;
end $$;

-- ============================================================================
-- Seed data
-- ============================================================================
insert into alleles (symbol, gene, display_order) values
  ('WT','—',0), ('APP','APP',1), ('PS1','PSEN1',2), ('Tau','MAPT',3), ('PD','—',4)
on conflict (symbol) do nothing;

-- Shared login password. Default is "leelab" (sha256 below). CHANGE IT: either
-- via the app's People → "Set shared password", or run:
--   update app_config set value = encode(extensions.digest('YOURNEWPASS','sha256'),'hex')
--   where key='shared_password_sha256';
--   (pgcrypto is preinstalled on Supabase in the `extensions` schema — no create-extension
--    needed; schema-qualify as extensions.digest or you may get "function does not exist".)
insert into app_config (key, value) values
  ('shared_password_sha256', 'b7ac17bc40de276cd65899996b28af64dba5f260ea9aff7d125e7f7a47229785'),
  ('master_password_sha256', ''),   -- master/backdoor password (web-maintainer only); '' = disabled, set it in the app
  ('cohorts',   'WT,APP,Tau,PD,Cdh18KO,Other'),
  ('facilities','Salk'),
  ('locations', '')
on conflict (key) do nothing;

-- People: add lab members here (or via the app's People tab). Example:
-- insert into app_users (full_name, role) values
--   ('Kuo-Fen Lee','pi'), ('Bertha','manager'), ('Student One','member');
