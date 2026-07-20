// Lee Lab Colony — request notification email sender (Supabase Edge Function).
//
// Deploy:  supabase functions deploy notify-request --no-verify-jwt
// Secrets: RESEND_API_KEY (required), EMAIL_FROM (e.g. "Lee Lab Colony <colony@kuofenleelab.com>"),
//          APP_URL (optional, link included in the email).
//          SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are injected automatically.
//
// The client sends only { requestId }. Recipients are the request's OWN
// assignees (requests.assignee_ids), resolved to emails SERVER-SIDE from
// app_users — never a client-supplied address list — and the body is composed
// from the stored request. So it can only email a request's assignees, not act
// as an open relay.

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
    const { requestId } = await req.json().catch(() => ({}));
    if (!requestId) return json({ error: "requestId required" }, 400);

    const SUPABASE_URL = Deno.env.get("SUPABASE_URL");
    const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
    const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY");
    const EMAIL_FROM = Deno.env.get("EMAIL_FROM") || "Lee Lab Colony <onboarding@resend.dev>";
    const APP_URL = Deno.env.get("APP_URL") || "https://leomeow123.github.io/leelab-colony/"; // link always appears even if the secret isn't set
    if (!RESEND_API_KEY) return json({ error: "RESEND_API_KEY not set" }, 500);
    if (!SUPABASE_URL || !SERVICE_KEY) return json({ error: "Supabase env missing" }, 500);

    const db = createClient(SUPABASE_URL, SERVICE_KEY);

    const { data: r, error: e1 } = await db.from("requests")
      .select("subject, body, needed_sex, needed_cohort, quantity, status, requester_id, assignee_id, assignee_ids, created_at")
      .eq("id", requestId).single();
    if (e1 || !r) return json({ error: "request not found" }, 404);

    // Replay guard: only notify freshly-created requests (blocks looping an old, known requestId).
    if (r.created_at && Date.now() - new Date(r.created_at).getTime() > 15 * 60 * 1000)
      return json({ error: "request too old to notify" }, 409);

    // Recipients = the request's OWN assignees (assignee_ids, else the single assignee_id),
    // resolved to emails from app_users. Nothing comes from the caller.
    const ids: string[] = (Array.isArray(r.assignee_ids) && r.assignee_ids.length)
      ? r.assignee_ids : (r.assignee_id ? [r.assignee_id] : []);
    if (ids.length === 0) return json({ sent: 0, missing: [] });

    const emails = new Set<string>();
    const missing = new Set<string>();
    const EMAIL_RE = /^[^\s@,;"<>]+@[^\s@,;"<>]+\.[^\s@,;"<>]+$/;
    const { data: users } = await db.from("app_users").select("full_name,email").in("id", ids);
    (users || []).forEach((u: { full_name?: string; email?: string | null }) => {
      const e = (u.email || "").trim();
      if (e && EMAIL_RE.test(e)) emails.add(e); else missing.add(u.full_name || "someone");
    });
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

    // HTML version so the colony app is a real clickable link/button (not just text).
    const esc = (s: unknown) => String(s ?? "").replace(/[&<>"]/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c] as string));
    const html =
`<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;font-size:14px;color:#1a1d26;line-height:1.5">
  <p>A mouse request was filed in the Lee Lab colony DB:</p>
  <table style="margin:8px 0;border-collapse:collapse">
    <tr><td style="padding:2px 8px 2px 0;color:#667085">Request</td><td><b>${esc(r.subject)}</b></td></tr>
    ${r.body ? `<tr><td style="padding:2px 8px 2px 0;color:#667085">Details</td><td>${esc(r.body)}</td></tr>` : ""}
    <tr><td style="padding:2px 8px 2px 0;color:#667085">Criteria</td><td>Genotype: ${esc(r.needed_cohort || "any")} · Sex: ${esc(r.needed_sex || "any")} · Qty: ${esc(r.quantity || "—")}</td></tr>
    <tr><td style="padding:2px 8px 2px 0;color:#667085">Status</td><td>${esc(r.status)}</td></tr>
    <tr><td style="padding:2px 8px 2px 0;color:#667085">Filed by</td><td>${esc(by)}</td></tr>
  </table>
  ${APP_URL ? `<p style="margin-top:16px">
    <a href="${esc(APP_URL)}" style="display:inline-block;background:#2563eb;color:#fff;text-decoration:none;padding:9px 16px;border-radius:8px;font-weight:600">Open the colony app →</a>
  </p>
  <p style="color:#667085;font-size:12px">Or paste this link: <a href="${esc(APP_URL)}">${esc(APP_URL)}</a></p>` : ""}
</div>`;

    const send = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: "Bearer " + RESEND_API_KEY, "Content-Type": "application/json" },
      body: JSON.stringify({ from: EMAIL_FROM, to, subject, text, html }),
    });
    if (!send.ok) return json({ error: "resend: " + (await send.text()) }, 502);
    return json({ sent: to.length, missing: [...missing] }); // counts/names only — don't echo addresses
  } catch (e) {
    return json({ error: String(e) }, 500);
  }
});
