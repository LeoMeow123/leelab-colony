# Lee Lab Mouse Colony DB

### 🔗 Live: https://leomeow123.github.io/leelab-colony/
*(moves to https://colony.kuofenleelab.com once the DNS record is added.)*
Log in with your name + the shared lab password.

A single-file web app (`index.html`) + Postgres schema (`schema.sql`) for the
Kuo-Fen Lee lab mouse colony. Backed by Supabase (Postgres + auto REST API + RLS),
hosted on GitHub Pages, with automated daily backups in a separate private repo.

**Features:** browse / search / filter / sort the colony, per-mouse timeline,
add & edit mice, people admin, CSV export, and a **request/approval queue**
(ask an owner for mice or route to breeding, with comments + ownership transfer).

## Login model (kept deliberately simple)
Everyone picks their **name** from a dropdown and types **one shared lab
password**. Your name is attached to every edit (audit trail). This is a *soft*
gate for internal use — it is not per-user security, and anyone with the link +
password + the public key can edit. When you want real accounts later, we swap in
Supabase Auth (magic-link or Google SSO) **without changing the schema**.

## One-time setup (~10 min)
1. **Create a Supabase project** (supabase.com → New project; free tier is fine for now). Pick a region near Salk (West US).
2. **Run the schema:** Supabase → SQL Editor → New query → paste all of `schema.sql` → Run. (Run it once.) `schema.sql` already includes the cohort columns; **if you set up before those existed, also run `migration_001.sql` once** (safe to re-run — the app shows a banner if it's missing).
3. **Add people:** either in the app's **People** tab after logging in, or in SQL:
   ```sql
   insert into app_users (full_name, role) values
     ('Kuo-Fen Lee','pi'), ('Bertha','manager'), ('Student One','member');
   ```
4. **Default password is `leelab`** — change it in the app (People → *Set shared password*) or via SQL.
5. **Get your keys:** Supabase → Project Settings → **API** → copy the **Project URL** and the **anon / publishable** key (NOT the service_role/secret key).
6. **Open the app** (`index.html` or the hosted URL). On first load it asks for the URL + key — paste them; they're saved in your browser. (Once you send me the two values I can hardcode them so nobody has to paste.)

## Using it
- **Colony tab:** filter by search (tag/genotype), sex, cohort, **facility**, status, age window (months), owner, location; click any column header to sort; click a row for the detail + timeline; **CSV** exports the current filtered set.
- **Add cohort:** enter a whole cage/cohort at once — required **Genotype, Owner, Sex (by count: # male / female / unknown), and Age**. Mouse numbers can be left **blank (pending)** and auto-file an **ear-tag request**, or entered as a list/range (`4471-4478`). Age is either a real **DOB** or a **rough age → computed DOB flagged as estimated** (`~` in the list, editable later) or deferred (*Unknown, add later*). Location is structured: **Facility → Room → Rack → Row/Col (single or range) → # cages**.
- **Mouse detail:** view/edit fields, "✓ mark verified today" (feeds the `stale >30d` badge), and a merged **timeline** (birth → experiments → procedures → death).
- **People:** add lab members and set the shared password.

## What's stored
Normalized Postgres: `mice` (hub; `id` = the only global key, `tag_id` = non-unique
ear-tag), `mouse_v` view (adds derived age + staleness), `app_users`, `alleles`,
`experiments` + `experiment_mice`, `procedures`, `requests` (Phase 2), `raw_import`
(Phase 2 import staging), `audit_log`. See `schema.sql`.

## Not in Phase 1 yet (coming next)
- **Excel/PDF import** with Claude extraction → review screen → bulk insert (`raw_import` table is ready).
- **Request/approval queue** with email routing to owners + Bertha (`requests` table is ready).
- Experiment-enrollment UI and breeding/lineage.

## Two things I still need from you (to make the data correct)
1. **Ear-tag uniqueness:** do tag / cage-card numbers repeat across cohorts / years / facilities? (Decides dedup rules for import.)
2. **The exact genotypes/alleles** the lab uses (I seeded WT / APP / PS1 / Tau / PD — tell me the real set and I'll fix the cohort vocab).
