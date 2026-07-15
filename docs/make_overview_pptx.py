#!/usr/bin/env python3
"""Generate a brief overview deck (flowcharts + bullets) for the Lee Lab Colony DB."""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

# palette
BLUE   = RGBColor(0x25, 0x63, 0xEB)
DBLUE  = RGBColor(0x1E, 0x3A, 0x8A)
GREEN  = RGBColor(0x15, 0x80, 0x3D)
AMBER  = RGBColor(0xB4, 0x53, 0x09)
PURPLE = RGBColor(0x7C, 0x3A, 0xED)
SLATE  = RGBColor(0x33, 0x41, 0x55)
GREY   = RGBColor(0x64, 0x74, 0x8B)
LIGHT  = RGBColor(0xEF, 0xF3, 0xFB)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
INK    = RGBColor(0x1A, 0x1D, 0x26)

prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
SW = prs.slide_width


def slide():
    return prs.slides.add_slide(BLANK)


def txt(sl, s, l, t, w, h, size=18, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, italic=False):
    tb = sl.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = s
    f = r.font; f.size = Pt(size); f.bold = bold; f.italic = italic; f.color.rgb = color; f.name = "Calibri"
    return tb


def header(s, title, sub=None):
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SW, Inches(1.05))
    bar.fill.solid(); bar.fill.fore_color.rgb = DBLUE; bar.line.fill.background()
    tf = bar.text_frame; tf.margin_left = Inches(0.5); tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; r = p.add_run(); r.text = title
    r.font.size = Pt(26); r.font.bold = True; r.font.color.rgb = WHITE; r.font.name = "Calibri"
    if sub:
        txt(s, sub, 0.52, 1.1, 12.4, 0.4, size=13, color=GREY, italic=True)


def box(s, l, t, w, h, text, fill=BLUE, font=WHITE, size=13, bold=True, rounded=True, line=None):
    shp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
                             Inches(l), Inches(t), Inches(w), Inches(h))
    shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line; shp.line.width = Pt(1)
    tf = shp.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.08); tf.margin_right = Inches(0.08); tf.margin_top = Inches(0.04); tf.margin_bottom = Inches(0.04)
    for i, ln in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = ln
        r.font.size = Pt(size if i == 0 else size - 2); r.font.bold = bold if i == 0 else False
        r.font.color.rgb = font; r.font.name = "Calibri"
    return shp


def arrow(s, l, t, w, h, direction="right", color=GREY):
    m = {"right": MSO_SHAPE.RIGHT_ARROW, "down": MSO_SHAPE.DOWN_ARROW, "left": MSO_SHAPE.LEFT_ARROW}
    a = s.shapes.add_shape(m[direction], Inches(l), Inches(t), Inches(w), Inches(h))
    a.fill.solid(); a.fill.fore_color.rgb = color; a.line.fill.background()
    return a


def bullets(s, l, t, w, h, items, size=16, color=INK, gap=6):
    tb = s.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    for i, it in enumerate(items):
        lvl = 0; text = it
        if isinstance(it, tuple):
            lvl, text = it
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = lvl; p.space_after = Pt(gap)
        r = p.add_run(); r.text = ("• " if lvl == 0 else "– ") + text
        r.font.size = Pt(size if lvl == 0 else size - 2); r.font.color.rgb = color; r.font.name = "Calibri"
        r.font.bold = (lvl == 0 and text.endswith(":"))
    return tb


# ---------------------------------------------------------------- Slide 1: title
s = slide()
bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SW, prs.slide_height)
bg.fill.solid(); bg.fill.fore_color.rgb = DBLUE; bg.line.fill.background()
txt(s, "🐭 Lee Lab Mouse Colony Database", 1, 2.4, 11.3, 1.2, size=40, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
txt(s, "How it works — architecture, multi-user access & email notifications",
    1, 3.7, 11.3, 0.8, size=20, color=RGBColor(0xC7, 0xD6, 0xF5), align=PP_ALIGN.CENTER)
txt(s, "Single-page web app  +  Supabase (Postgres)  •  hosted free on GitHub Pages  •  daily backups",
    1, 5.2, 11.3, 0.6, size=14, color=RGBColor(0x9F, 0xB4, 0xE0), align=PP_ALIGN.CENTER)

# ---------------------------------------------------------------- Slide 2: architecture
s = slide()
header(s, "The pipeline — how it runs", "No server to maintain: a static web page talks straight to a hosted database.")
y = 1.9; bw = 2.75; bh = 1.3
box(s, 0.5, y, bw, bh, "Lab member\n(browser: laptop / phone)", fill=SLATE)
arrow(s, 3.35, y+0.45, 0.5, 0.4)
box(s, 3.95, y, bw, bh, "GitHub Pages\nserves index.html\n(one HTML file, free)", fill=BLUE)
arrow(s, 6.8, y+0.45, 0.5, 0.4)
box(s, 7.4, y, 3.0, bh, "Supabase\nPostgres DB + auto REST API\n+ Row-Level Security", fill=GREEN)
# data store under supabase
arrow(s, 8.7, y+1.35, 0.4, 0.4, direction="down")
box(s, 7.4, y+1.85, 3.0, 0.9, "mice • app_users • requests\naudit_log • app_config", fill=RGBColor(0x0F,0x5A,0x2E), size=12)
# backups branch
arrow(s, 10.5, y+0.45, 0.45, 0.4)
box(s, 11.0, y, 2.0, bh, "GitHub Actions\ndaily backup\nsnapshots", fill=AMBER, size=12)

bullets(s, 0.6, 4.9, 12.2, 2.4, [
    "Browser loads one self-contained index.html — no build, no backend to run.",
    "It calls Supabase directly with a public (publishable) key; Row-Level Security controls access.",
    "Postgres stores everything; a mouse_v view derives age & staleness from date-of-birth.",
    "A daily GitHub Action dumps every table to a private repo (restorable snapshots) and keeps the free DB awake.",
], size=15)

# ---------------------------------------------------------------- Slide 3: data flow
s = slide()
header(s, "What flows through it", "From data entry to finding a mouse.")
y = 1.85; bh = 1.15
box(s, 0.5, y, 3.0, bh, "ADD\nAdd cohort by cage\n(sex • age/DOB • strain • cage #)", fill=BLUE, size=12)
box(s, 0.5, y+1.5, 3.0, bh, "IMPORT\nCSV / Excel → map → preview", fill=BLUE, size=12)
arrow(s, 3.6, y+1.0, 0.5, 0.5)
box(s, 4.25, y+0.35, 2.5, 1.6, "mice table\n(+ mouse_v view:\nage, staleness)", fill=GREEN, size=13)
arrow(s, 6.85, y+1.0, 0.5, 0.5)
box(s, 7.5, y-0.1, 5.3, 2.4,
    "BROWSE & MANAGE\n\n"
    "• Search / filter / sort • Individual & Grouped views\n"
    "• My colony (your cohorts) • batch edit\n"
    "• Modify a cohort: add / remove / renumber\n"
    "• Requests & approvals",
    fill=SLATE, size=12, bold=False)
box(s, 0.5, y+3.15, 12.3, 0.7, "Every create / edit / delete is attributed to a user and written to the audit_log",
    fill=AMBER, size=13)
bullets(s, 0.6, 6.35, 12.2, 1.0, [
    "Genotype = WT / Tau / … (controlled) · Strain = C57BL/6 / hMAP · Location = Facility→Room→Rack→Row/Col→Cage.",
], size=13, color=GREY)

# ---------------------------------------------------------------- Slide 4: multiple users
s = slide()
header(s, "Multiple users", "Simple shared login now; upgradeable to real accounts later.")
y = 1.9; bh = 1.15
box(s, 0.5, y, 3.4, bh, "Pick your name\n+ shared lab password", fill=BLUE, size=13)
arrow(s, 4.0, y+0.35, 0.5, 0.45)
box(s, 4.6, y, 3.4, bh, "First login only:\nenter your email once", fill=PURPLE, size=13)
arrow(s, 8.1, y+0.35, 0.5, 0.45)
box(s, 8.7, y, 4.1, bh, "Use the app — every edit\ntagged with your name", fill=GREEN, size=13)
bullets(s, 0.6, 3.5, 12.2, 3.4, [
    "Roles: PI · Manager · Member (drive request routing & who can approve).",
    "Identity is remembered in your browser; your name is stamped on every change (audit trail).",
    "Your saved email is used for notifications (set once, never asked again).",
    "Security model:",
    (1, "Internal shared password + one public key — a soft gate for a trusted lab, not per-person security."),
    (1, "Anyone with the link + password can view/edit; all actions are logged."),
    (1, "Upgrade path: swap in real per-user accounts (magic-link / Google SSO) with no schema change."),
], size=15)

# ---------------------------------------------------------------- Slide 5: email/requests
s = slide()
header(s, "Requests & email notifications", "Ask for mice; the right people get emailed automatically.")
y = 1.75; bh = 1.15
box(s, 0.4, y, 2.7, bh, "Member files a request\n(specific mouse # or by criteria)", fill=BLUE, size=12)
arrow(s, 3.2, y+0.35, 0.45, 0.45)
box(s, 3.75, y, 2.7, bh, "App finds a matching\nlive mouse → its Owner", fill=GREEN, size=12)
arrow(s, 6.55, y+0.35, 0.45, 0.45)
box(s, 7.1, y, 2.7, bh, "None available →\nBreeding queue (Manager)", fill=AMBER, size=12)
# notify row
arrow(s, 5.0, y+1.2, 0.4, 0.45, direction="down")
box(s, 2.6, y+1.75, 5.2, 1.0, "Choose who to notify:  Owner · Managers · PI", fill=PURPLE, size=13)
arrow(s, 7.9, y+2.1, 0.5, 0.45)
box(s, 8.5, y+1.55, 4.4, 1.45,
    "notify-request  (Supabase Edge Function)\nresolves emails server-side → Resend → sends",
    fill=DBLUE, size=12)
box(s, 8.5, y+3.15, 4.4, 0.75, "If not deployed → opens a pre-filled draft email (fallback)",
    fill=GREY, size=11, bold=False)
bullets(s, 0.5, 5.05, 7.7, 2.2, [
    "Recipients & message are built server-side from the stored request —",
    (1, "the app never sends a raw address list (can't be an open relay)."),
    "Guards: request-must-be-recent (replay), optional API-key check.",
    "Works with zero setup via the draft popup; turn on auto-send with a Resend key.",
], size=14)

# ---------------------------------------------------------------- Slide 6: recap
s = slide()
header(s, "In one line each")
bullets(s, 0.7, 1.7, 12.0, 5.2, [
    "Hosting:  one HTML file on GitHub Pages — free, nothing to run.",
    "Data:  Supabase Postgres, reached directly via its auto REST API + Row-Level Security.",
    "Entry:  add cohorts by cage, or import CSV/Excel with a mapping + preview step.",
    "Find:  search / filter / sort, Individual or Grouped views, and a personal 'My colony'.",
    "Edit:  per-mouse, in bulk, or whole-cohort (add / remove / renumber) — all audit-logged.",
    "Users:  name + shared password, per-user email captured once, every action attributed.",
    "Notify:  requests email Owner / Managers / PI via an Edge Function + Resend (draft fallback).",
    "Safety:  daily off-site backups; keep-alive so the free database never sleeps.",
], size=17, gap=10)

out = "/home/exx/leelab-colony/docs/Colony_DB_Overview.pptx"
prs.save(out)
print("saved", out, "slides:", len(prs.slides._sldIdLst))
