# Lee Lab Colony DB — how it works (Supabase, logins, roles, per-user views)

A plain-language explanation of the app's architecture.

## The big idea: no server of our own

A typical web app has three parts: a webpage (frontend), a server you write and
run (backend), and a database. Our colony app **skips the middle one**. There are
only two pieces:

1. **`index.html`** — one file, served by GitHub Pages. This *is* the whole app;
   it runs in each person's browser.
2. **Supabase** — a database in the cloud that the webpage talks to directly.

When you click "Add cohort," your browser sends the data straight to Supabase over
the internet. There's no server we maintain in between — which is why it's free
and low-maintenance.

## What Supabase actually is

Supabase is a **hosted PostgreSQL database with a few things bolted on** so a
browser can use it safely. The parts we use:

### 1. PostgreSQL (the database)
All data lives here, in tables:
- `mice` — the main table, one row per mouse (tag, sex, genotype, strain, DOB,
  owner, location/cage, status, experiments…).
- `mouse_v` — a *view* over `mice` that adds computed age + a "stale" flag.
- `app_users` — the people (name, **role**, email, and each person's **own
  password hash** + a "must set a password" flag).
- `requests` (+ `request_comments`) — the task / ask-for-mice queue.
- `guardian_angels` — lab members' pet photos; `angel_reactions` — the ❤️🥰🤗😢
  reactions people leave on them.
- `audit_log` — a record of every change (who did what, when).
- `app_config` — settings: the **default** and **master** password hashes, and the
  genotype / facility lists.

### 2. The auto-generated REST API (the clever part)
Normally you need a backend to query a database. Supabase runs a tool
(**PostgREST**) that automatically turns every table into a web address, e.g.:

```
https://xgiqhkcp….supabase.co/rest/v1/mice
```

The browser makes normal web requests to that URL:
- **GET** to read, **POST** to add, **PATCH** to edit, **DELETE** to remove.
- You can filter in the URL, e.g. `mice?status=eq.healthy&cohort=eq.WT`
  = "healthy WT mice."

Every search, add, and edit in the app is one of these URL calls. No hand-written
backend needed.

### 3. The key + Row-Level Security (the auth model)
Every request carries a **publishable key** (`sb_publishable_…`) that says "this is
the Lee Lab project." That key is *public* — it's visible in the page source — so
the key alone isn't security; it just identifies the project.

The real gatekeeper is **Row-Level Security (RLS)** — a Postgres feature that
decides, per row, who may read/write, via "policies." **Our policies are
deliberately permissive** (open read, open write on the tables we chose). So the
logins, roles, and ownership rules below are enforced by the *app*, not yet by the
database — the **"soft" security model**. Every action is stamped with a name and
logged, and RLS is exactly the lever we'd tighten later for real per-person
enforcement.

### 4. Views (`mouse_v`) — computed fields
A "view" is a saved query that looks like a table but calculates things live. We
never store a mouse's age (it would go stale daily); instead `mouse_v` computes
**age from date-of-birth on the fly** every read, plus a "stale" flag. The app
reads from `mouse_v`, so age is always current.

### 5. Edge Functions — the one bit that needs a server
Sending email needs a *secret* key (Resend), and you can't put a secret in a
public webpage. So Supabase lets you run a tiny server-side function — the
`notify-request` **Edge Function**. It holds the mail secret, works out who to
email (a request's assignees), and sends — with a clickable link back to the app.
It's the only "backend code" in the project, and it only runs for email.

### 6. Backups + keep-alive
A scheduled GitHub Action (in the private `leelab-colony-backups` repo) dumps
**every table to versioned JSON once a day** — including pets and reactions —
restorable via `scripts/restore.mjs`. The daily ping also keeps the free database
from sleeping after inactivity. A missing table (a migration not yet run) is
skipped, not fatal.

## Logins & passwords

Everyone picks their **name** and types **their own password**:
- **First time:** sign in with the shared **default** password once → the app
  **forces you to set a personal password** before it opens. After that, only you
  (with your password) can get into your account.
- **The Web-maintainer (Leo) has two backdoors:** a **"Log in as →"** button in
  People (log in as yourself, then step into anyone's view — no shared secret,
  written to the audit log), and a **master password** that works on any account
  as a break-glass. Both are visible only to the Web-maintainer.

Passwords are stored as SHA-256 **hashes** in `app_users` (never the plain text).
Because the anon key can read that table, this is still access *hygiene*, not a
vault — see the honest caveat below.

## The roles

Every person in `app_users` has a **role**, and the role changes what they can do:

- **Member** — files requests, adds/imports mice, and manages **their own** colony
  (edit / delete only their own mice).
- **Manager** — all of the above, **plus** approve/deny requests, transfer
  ownership, and act on any mouse. (The colony/breeding manager — e.g. Bertha.)
- **PI** — same authority as a manager, for oversight.
- **Web maintainer** — full access (Leo), plus the password/impersonation
  backdoors. The label marks who runs the site, separate from the colony manager.

## Why different users see (and can do) different things

It's the **same database and the same key for everyone**, yet the experience
differs — because the *app* shapes each person's view using **who owns a mouse**,
**your role**, and **who you're logged in as**:

- **"My colony"** asks the database only for rows where you're the owner or
  creator — so you see and manage *your* cohorts, grouped as you like (by cohort /
  genotype / age / status), expandable to individual mice.
- **Delete and batch-edit are owner-scoped.** A member can only delete or bulk-edit
  mice they own/created (enforced with a server-side owner filter); managers / PI /
  Web-maintainer can act on any. Bulk delete lives in "My colony."
- **Requests are assigned to specific people you pick**; approve / transfer /
  close buttons render only for a Manager, PI, Web-maintainer, or the request's
  assignees. Only the assignees are emailed.
- **The password backdoors and setters are Web-maintainer-only** — other users
  don't even see them.

**Honest caveat (worth saying to the lab):** this is still *presentation-level*
differentiation, not hard security. Everyone shares one public key, and the
password hashes live in a table that key can read (unsalted SHA-256), so a
determined technical person could bypass the UI. What protects us in practice:
per-user passwords stop casual cross-login, roles/ownership decide what the UI
shows and who can act, **and every change is written to the audit log**. For true
per-person enforcement (the database itself refusing unauthorized access), we'd
switch to **Supabase Auth** (magic-link / Google) and write those rules into RLS —
**with no change to the data or tables**. That upgrade path is why the schema was
built this way.

## The lab-morale extras

Beyond the data, the app tries to be a nice place to visit:
- **😇 Guardian Angels** — everyone uploads their pets (resized to a small image in
  the browser, so no file-storage setup is needed). They watch over the top of the
  Colony page.
- **A warm greeting on every visit** — a random guardian angel pops up with a
  species sound (cat → *meow~*), the San-Diego date/time, and an encouraging
  message. You can leave a reaction (recorded once a day; the message shows anytime).
- **🕯️ In Memoriam** — a gentle memorial for departed (dead / sacrificed /
  collected) mice, honoring their contribution to the science.

## One concrete trip through it

Malia files a request for "2 female WT mice":

1. Her browser POSTs the request to `…/rest/v1/requests` with the public key.
2. The app finds a match and sets the request's assignee to that owner (or the
   breeding manager if none).
3. She picks who to assign it to; the app calls the `notify-request` Edge Function,
   which looks up those people's emails **server-side** and sends via Resend with a
   link back to the app.
4. The whole thing is recorded in `audit_log`.

That's the entire system: a webpage talking directly to a hosted Postgres via
auto-generated URLs, with logins + roles + ownership shaping what each person sees
and can do, and one small server-side function for email.
