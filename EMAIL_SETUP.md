# Automated email notifications (optional)

The app already notifies people by opening a **pre-filled email draft** (the
mail-client popup) — that works with zero setup. This adds *automatic* sending
so a notification goes out silently, even when the requester's mail client
isn't set up. Until you finish these steps, the app just keeps using the draft
popup (graceful fallback), so nothing breaks in the meantime.

**How it works:** the browser can't hold a mail-provider secret, so a small
**Supabase Edge Function** (`supabase/functions/notify-request/`) does the send
via **[Resend](https://resend.com)**. The client only sends `{requestId}`; the
function looks up that request's **assignees** (`assignee_ids`), resolves their
emails from `app_users`, and composes the message server-side — so it can only
email a request's own assignees, not an arbitrary address list.

## 1. Resend account + API key
1. Sign up at **resend.com** (free tier: 100 emails/day, 3,000/mo).
2. **API Keys → Create** → copy the key (`re_...`).
3. **Sending domain:**
   - *Quick test:* skip domain setup and use the built-in sender
     `onboarding@resend.dev`. **Resend test mode only delivers to your own
     Resend account email**, so this is only good for a first test.
   - *Real use:* **Domains → Add domain** → `kuofenleelab.com` (or a subdomain
     like `mail.kuofenleelab.com`) → add the shown DNS records (SPF/DKIM) at
     your DNS host → verify. Then send from e.g.
     `Lee Lab Colony <colony@kuofenleelab.com>`.

## 2. Deploy the function
**Option A — Supabase dashboard (no CLI):** Project → **Edge Functions** →
*Create a function* → name it **`notify-request`** → paste the contents of
`supabase/functions/notify-request/index.ts` → **Deploy**. Then in the
function's settings turn **"Verify JWT" OFF** (the app uses a publishable key,
which isn't a JWT).

**Option B — CLI:**
```bash
supabase login
supabase link --project-ref xgiqhkcpssakrlemvodx
supabase functions deploy notify-request --no-verify-jwt
```

## 3. Set the secrets
Dashboard → **Edge Functions → Manage secrets** (or `supabase secrets set …`):
- `RESEND_API_KEY` = your `re_...` key  **(required)**
- `EMAIL_FROM` = `Lee Lab Colony <colony@kuofenleelab.com>` (or `onboarding@resend.dev` for the test)
- `APP_URL` = `https://leomeow123.github.io/leelab-colony/` (the email now shows a clickable "Open the colony app" button linking here; if unset it defaults to this URL)
- `ALLOWED_APIKEY` = your publishable key `sb_publishable_...` (optional but recommended) — if set, the function rejects callers that don't send it, so the endpoint isn't openly invokable. The app already sends it.

`SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are provided to the function
automatically — you don't set those.

## 4. Test
File a request in the app with **Notify** checked. If the function is live, you
get a toast like *"emailed 2 people"* and no draft popup. If anything isn't
ready, the app silently falls back to the draft-email popup.

## Notes
- Everyone must have set their email (first-login prompt) to receive mail;
  people without one are listed in the toast as "no email yet".
- To turn it off, just delete the function — the app reverts to draft popups.
- Import-help still uses a draft email on purpose (it needs you to attach the file).
