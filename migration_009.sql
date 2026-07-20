-- ============================================================================
-- Migration 009 — reactions to Guardian Angels (for the warm login greeting).
-- Run ONCE in the Supabase SQL editor. Safe to re-run.
-- ============================================================================

create table if not exists angel_reactions (
  id uuid primary key default gen_random_uuid(),
  angel_id uuid references guardian_angels(id) on delete cascade,
  user_id uuid references app_users(id),
  reaction text,                       -- love / cute / care / sad
  created_at timestamptz default now()
);
create index if not exists angel_reactions_angel_idx on angel_reactions(angel_id);

grant select, insert, update, delete on angel_reactions to anon, authenticated;
alter table angel_reactions enable row level security;
drop policy if exists angel_reactions_sel on angel_reactions;
create policy angel_reactions_sel on angel_reactions for select using (true);
drop policy if exists angel_reactions_ins on angel_reactions;
create policy angel_reactions_ins on angel_reactions for insert with check (true);
drop policy if exists angel_reactions_del on angel_reactions;
create policy angel_reactions_del on angel_reactions for delete using (true);
