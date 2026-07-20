-- ============================================================================
-- Migration 007 — 'collected' status + Guardian Angels (lab pets).
-- Run ONCE in the Supabase SQL editor. Safe to re-run.
-- ============================================================================

-- 1) Add 'collected' to the mouse status vocabulary (mice collected for tissue/organs).
alter table mice drop constraint if exists mice_status_check;
alter table mice add constraint mice_status_check
  check (status in ('healthy','diseased','sacrificed','dead','transferred','collected','unknown'));

-- 2) Guardian Angels — lab members' pets that "watch over" the colony.
--    Photos are stored as a resized base64 data-URL (client-side compressed), so
--    no Storage bucket setup is needed — it rides the same REST API as everything else.
create table if not exists guardian_angels (
  id uuid primary key default gen_random_uuid(),
  name text not null,                       -- the pet's name
  species text,                             -- dog / cat / hamster / …
  owner_id uuid references app_users(id),   -- whose pet it is
  owner_name text,                          -- denormalized for display
  message text,                             -- a caption / blessing
  photo text,                               -- data-URL (base64 JPEG, resized in the browser)
  created_by uuid references app_users(id),
  created_at timestamptz default now()
);

-- grants + permissive RLS (same soft model as the rest of the app)
grant select, insert, update, delete on guardian_angels to anon, authenticated;
alter table guardian_angels enable row level security;
drop policy if exists guardian_angels_sel on guardian_angels;
create policy guardian_angels_sel on guardian_angels for select using (true);
drop policy if exists guardian_angels_ins on guardian_angels;
create policy guardian_angels_ins on guardian_angels for insert with check (true);
drop policy if exists guardian_angels_upd on guardian_angels;
create policy guardian_angels_upd on guardian_angels for update using (true) with check (true);
drop policy if exists guardian_angels_del on guardian_angels;
create policy guardian_angels_del on guardian_angels for delete using (true);
