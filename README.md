# Lee Lab Mouse Colony DB

### 🔗 Live: https://leomeow123.github.io/leelab-colony/
*(moves to https://colony.kuofenleelab.com once the DNS record is added.)*
Log in with your name + the shared lab password.

A single-file web app (`index.html`) + Postgres schema (`schema.sql`) for the
Kuo-Fen Lee lab mouse colony. Backed by Supabase (Postgres + auto REST API + RLS),
hosted on GitHub Pages, with automated daily backups in a separate private repo.

**Features:** browse / search / filter / sort the colony (individual **or** grouped),
per-mouse timeline, add mice one at a time or a whole cohort, **CSV/Excel import**
with automatic column-matching, per-cohort **batch edit**, **owner-scoped**
edit/delete, a **request/approval queue** with a dedicated **“Mice needed”
breeding board** and automatic email, an **🕯️ In Memoriam** memorial for departed
mice, a **😇 Guardian Angels** wall of the lab’s pets, CSV export, people admin,
and a full audit log.

## Login model
Everyone picks their **name** and types **their own password**. New people sign in
with the **default password once**, then are **forced to set a personal password**
so no one can log into someone else's account. The **Web-maintainer** has two
backdoors: **"Log in as →"** impersonation from People (no shared secret, audited)
and a **master password** that works on any account (break-glass). Every edit is
attributed (audit trail).

This is still a *soft* gate for internal use: the password hashes live in a table
the public key can read (unsalted SHA-256), so a technical person could bypass the
UI — it's access hygiene, not a vault. For **hard** per-user security, swap in
Supabase Auth (magic-link / Google SSO) later **without changing the schema**.

## Roles & permissions
Four roles: **Member**, **Manager**, **PI**, and **Web-maintainer** (full access).
Every edit is attributed and logged. **Deleting and batch-editing mice are
owner-scoped** — a member acts only on mice they own or created; managers / PI /
Web-maintainer can act on any. This is enforced in the UI (the soft model); dropping
in Supabase Auth + RLS later makes it hard enforcement **without schema changes**.

## One-time setup (~10 min)
1. **Create a Supabase project** (supabase.com → New project; free tier is fine for now). Pick a region near Salk (West US).
2. **Run the schema:** Supabase → SQL Editor → New query → paste all of `schema.sql` → Run. (Run it once.) `schema.sql` already includes the latest columns; **on an existing project, run the `migration_00*.sql` files in order** (001 cohort columns, 002 delete policy, 003 experiments + health status, 004 cage,
005 Web-maintainer role + multi-assignee requests, 006 request type + which-mice info,
   007 'collected' status + Guardian Angels pet table, 008 per-user + master passwords) — each is safe to re-run, and the app shows a banner if any is missing. (The app degrades gracefully until a migration is run — e.g. login falls back to the shared password until 008 is applied.)
3. **Add people:** either in the app's **People** tab after logging in, or in SQL:
   ```sql
   insert into app_users (full_name, role) values
     ('Kuo-Fen Lee','pi'), ('Bertha','manager'), ('Student One','member');
   ```
4. **Default password is `leelab`** — change it in the app (People → *Set shared password*) or via SQL.
5. **Get your keys:** Supabase → Project Settings → **API** → copy the **Project URL** and the **anon / publishable** key (NOT the service_role/secret key).
6. **Open the app** (`index.html` or the hosted URL). On first load it asks for the URL + key — paste them; they're saved in your browser. (The live site already has them hardcoded.)

## Using it
- **Colony** (home): search (tag / strain), sex, genotype, facility, status, age window, owner, location; sort by any column; **individual or grouped** view; click a row for the detail + timeline; **CSV** exports the filtered set. Status defaults to *any* so nothing a member adds is hidden. Guardian-angel pets watch over the top.
- **My colony:** just the cohorts you added / own. **Separate by** cohort / genotype / age / status, see an **age range** per group, **expand** any group into its individual mice, **batch-modify**, or **multi-select delete** — all scoped to your own mice.
- **Add cohort:** a whole cage/cohort at once, or toggle to **Single mouse**. Genotype is a **typeable combobox** (type a new one → it sticks); **Owner required**; Age = real **DOB** / rough age (→ estimated `~`) / *unknown*; structured location (Facility → Room → Rack → Row/Col, with an *“undecided”* option). Pending mouse numbers auto-file an ear-tag request.
- **Import (CSV/Excel):** we show the fields we need and **auto-match your columns** for you (your extra columns are ignored); **Owner** is a required picker (not read from the file); statuses like active/inactive/collected map automatically. An unreadable file → one-click “email it to Leo”.
- **Requests / Mice needed / My requests:** file a task (genotype, ear-tag, move, breed) or a **Request for mice**; assign it to one or more people (emailed via the Edge Function, with a link back to the app); the **Mice needed** board is the long-term breeding queue; a two-stage *done → close* lifecycle keeps a Completed archive.
- **🕯️ In Memoriam:** a memorial grid for dead / sacrificed / collected mice.
- **😇 Guardian Angels:** upload the lab’s pets (photo resized in-browser); they appear here and on the colony.
- **People:** add members, set roles, and set the shared password.

## What's stored
Normalized Postgres: `mice` (hub; `id` = the only global key, `tag_id` = non-unique
ear-tag), `mouse_v` view (adds derived age + staleness), `app_users`, `alleles`,
`experiments` + `experiment_mice`, `procedures`, `requests` (+ `request_comments`),
`guardian_angels` (pet photos as resized base64), `raw_import`, `audit_log`.
See `schema.sql`.

## Email notifications
Requests notify their assignees. Out of the box this opens a pre-filled email
**draft**; for fully **automatic** sending, deploy the `notify-request` Edge
Function + Resend — see **`EMAIL_SETUP.md`**. The email includes a clickable link
back to the app. Until deployed, the app falls back to the draft popup either way.

## Backups
A GitHub Action in the private **`leelab-colony-backups`** repo dumps every table
to versioned JSON once a day (~02:17 PT) — restorable via `scripts/restore.mjs` —
and the daily ping keeps the free project from auto-pausing.

## Coming next
- **Per-user accounts** (Supabase Auth) → real per-person permissions (and the
  ownership rules above become DB-enforced).
- Experiment-enrollment UI and breeding / lineage.
- PDF import (CSV/Excel already shipped).

## Still useful to confirm
- **Ear-tag uniqueness:** do tag / cage-card numbers repeat across cohorts / years /
  facilities? (Decides dedup rules for import.)
- The genotype vocab is now **editable in the app** (typeable genotype field; seeded
  WT / APP / Tau / PD / Cdh18KO / Other) — add the real set as you go.
