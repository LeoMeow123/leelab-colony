# Lee Lab Colony DB — how it works (Supabase, roles, per-user views)

A plain-language explanation to go with the overview deck.

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
  owner, location/cage, status…).
- `app_users` — the people (name, **role**, email).
- `requests` — the ask-for-mice queue.
- `audit_log` — a record of every change.
- `app_config` — settings (the shared-password hash, the genotype/facility lists).

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
deliberately permissive** (open read, open write on the tables we chose). Combined
with the shared password, that's the **"soft" security model**: anyone logged in
can technically touch anything — but every action is stamped with a name and
logged. RLS is exactly the lever we'd tighten later for real per-person
permissions.

### 4. Views (`mouse_v`) — computed fields
A "view" is a saved query that looks like a table but calculates things live. We
never store a mouse's age (it would go stale daily); instead `mouse_v` computes
**age from date-of-birth on the fly** every read, plus a "stale" flag. The app
reads from `mouse_v`, so age is always current.

### 5. Edge Functions — the one bit that needs a server
Sending email needs a *secret* key (Resend), and you can't put a secret in a
public webpage. So Supabase lets you run a tiny server-side function — the
`notify-request` **Edge Function**. It holds the mail secret, works out who to
email, and sends. It's the only "backend code" in the project, and it only runs
for email.

### 6. Backups + keep-alive
A scheduled GitHub Action logs into Supabase once a day, dumps every table to a
private repo (restorable if something breaks), and the daily ping also keeps the
free database from sleeping after inactivity.

## The roles

Every person in `app_users` has a **role**, and the role changes what they can do:

- **Member** — files requests, adds/imports mice, manages their own colony.
- **Manager** — all of the above, **plus** approve/deny requests, transfer
  ownership, and route to breeding. (The colony/breeding manager — e.g. Bertha.)
- **PI** — same authority as a manager, for oversight.
- **Web maintainer** — full access (Leo). Same powers as manager/PI; the label
  just marks who runs the site, separate from the colony manager.

## Why different users see different things

It's the **same database and the same key for everyone**, yet the experience
differs — because the *app* shapes each person's view using **who owns a mouse**
and **your role**:

- **"My colony" / the "Mine" filter** ask the database only for rows where
  `responsible_person = you` — so you see *your* mice, not everyone's.
- **Requests are assigned to specific people you pick** (grouped by role, with
  their email shown) — one or several. People without an email can still be
  assigned; they just aren't emailed.
- **Approve / transfer / route buttons render only for a Manager, PI, or Web
  maintainer** (or one of the request's assignees). A member doesn't see them.
- **Only a request's assignees are emailed** — the server looks up their
  addresses; no one else is contacted.

**Honest caveat (worth saying to the lab):** today this is *presentation-level*
differentiation, not hard security. With one shared password and one public key, a
determined logged-in person could read or edit anything. What protects us in
practice: roles/ownership decide what the UI shows and who can act, **and every
change is written to the audit log**. For true per-person enforcement (the
database itself refusing unauthorized edits), we'd add real logins (magic-link or
Google) and write those rules into Supabase RLS — **with no change to the data or
tables**. That upgrade path is why the schema was built this way.

## One concrete trip through it

Malia files a request for "2 female WT mice":

1. Her browser POSTs the request to `…/rest/v1/requests` with the public key.
2. The app GETs `mice?status=in.(healthy,diseased)&sex=eq.F&cohort=eq.WT` to find
   a match → gets the owner.
3. It sets the request's assignee to that owner (or the breeding manager if none).
4. She ticks "notify Owner + Managers," so the app calls the `notify-request` Edge
   Function, which looks up those people's emails **server-side** and sends via
   Resend.
5. The whole thing is recorded in `audit_log`.

That's the entire system: a webpage talking directly to a hosted Postgres via
auto-generated URLs, with roles + ownership shaping the view, and one small
server-side function for email.
