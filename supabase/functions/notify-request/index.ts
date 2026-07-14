// Lee Lab Colony — request notification email sender (Supabase Edge Function).
//
// Deploy:  supabase functions deploy notify-request --no-verify-jwt
// Secrets: RESEND_API_KEY (required), EMAIL_FROM (e.g. "Lee Lab Colony <colony@kuofenleelab.com>"),
//          APP_URL (optional, link included in the email).
//          SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are injected automatically.
//
// The client sends only { requestId, roles, ownerId }. Recipients are resolved
// SERVER-SIDE from app_users (never a client-supplied address list), and the
// message body is composed from the stored request — so this can only ever
// email known lab members about a real request, not act as an open relay.

import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.4";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, apikey, x-client-info, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (obj: unknown, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { ...cors, "Content-Type": "application/json" } });

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  // Optional shared-key gate: if ALLOWED_APIKEY is set, require it (the client sends the publishable key as `apikey`).
  const allowedKey = Deno.env.get("ALLOWED_APIKEY");
  if (allowedKey && (req.headers.get("apikey") || "") !== allowedKey) return json({ error: "unauthorized" }, 401);

  try {
    const { requestId, roles } = await req.json().catch(() => ({}));
    if (!requestId || !Array.isArray(roles) || roles.length === 0)
      return json({ error: "requestId and non-empty roles[] required" }, 400);

    const SUPABASE_URL = Deno.env.get("SUPABASE_URL");
    const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
    const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY");
    const EMAIL_FROM = Deno.env.get("EMAIL_FROM") || "Lee Lab Colony <onboarding@resend.dev>";
    const APP_URL = Deno.env.get("APP_URL") || "";
    if (!RESEND_API_KEY) return json({ error: "RESEND_API_KEY not set" }, 500);
    if (!SUPABASE_URL || !SERVICE_KEY) return json({ error: "Supabase env missing" }, 500);

    const db = createClient(SUPABASE_URL, SERVICE_KEY);

    const { data: r, error: e1 } = await db.from("requests")
      .select("subject, body, needed_sex, needed_cohort, quantity, status, requester_id, assignee_id, created_at")
      .eq("id", requestId).single();
    if (e1 || !r) return json({ error: "request not found" }, 404);

    // Replay guard: only notify freshly-created requests (blocks looping an old, known requestId).
    if (r.created_at && Date.now() - new Date(r.created_at).getTime() > 15 * 60 * 1000)
      return json({ error: "request too old to notify" }, 409);

    // Resolve recipients strictly from app_users, deduped. Owner is derived from the request's
    // assignee (server-side) — never a client-supplied id — so a caller can't target arbitrary people.
    const emails = new Set<string>();
    const missing = new Set<string>();
    const EMAIL_RE = /^[^\s@,;"<>]+@[^\s@,;"<>]+\.[^\s@,;"<>]+$/;
    const addUser = (u: { full_name?: string; email?: string | null } | null | undefined) => {
      if (!u) return;
      const e = (u.email || "").trim();
      if (e && EMAIL_RE.test(e)) emails.add(e); else missing.add(u.full_name || "someone");
    };
    if (roles.includes("owner") && r.status === "open" && r.assignee_id) {
      const { data } = await db.from("app_users").select("full_name,email").eq("id", r.assignee_id).maybeSingle();
      addUser(data);
    }
    if (roles.includes("managers")) {
      const { data } = await db.from("app_users").select("full_name,email").eq("role", "manager");
      (data || []).forEach(addUser);
    }
    if (roles.includes("pi")) {
      const { data } = await db.from("app_users").select("full_name,email").eq("role", "pi");
      (data || []).forEach(addUser);
    }
    const to = [...emails];
    if (to.length === 0) return json({ sent: 0, missing: [...missing] });

    let by = "someone";
    if (r.requester_id) {
      const { data } = await db.from("app_users").select("full_name").eq("id", r.requester_id).maybeSingle();
      if (data?.full_name) by = data.full_name;
    }

    const subject = "Mouse request: " + r.subject;
    const text =
`A mouse request was filed in the Lee Lab colony DB:

  ${r.subject}
  ${r.body || ""}
  Cohort: ${r.needed_cohort || "any"} · Sex: ${r.needed_sex || "any"} · Qty: ${r.quantity || "—"}
  Status: ${r.status}

Filed by ${by}.${APP_URL ? "\n\nOpen the colony app: " + APP_URL : ""}`;

    const send = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: "Bearer " + RESEND_API_KEY, "Content-Type": "application/json" },
      body: JSON.stringify({ from: EMAIL_FROM, to, subject, text }),
    });
    if (!send.ok) return json({ error: "resend: " + (await send.text()) }, 502);
    return json({ sent: to.length, missing: [...missing] }); // counts/names only — don't echo addresses
  } catch (e) {
    return json({ error: String(e) }, 500);
  }
});
