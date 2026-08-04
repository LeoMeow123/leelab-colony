# Plan — Virtual Room / Rack Map for the Lee Lab Colony

**Status:** draft for review · **Owner:** Leo · **Date:** 2026-08-04

Goal: a visual, navigable layout of the colony's physical space — enter a room,
see its racks, open a rack, and see the **cages** in a grid with **which mice /
cohorts** live in each spot. Start 2D and read-only; grow toward editing and an
optional 3D room view.

---

## 1. What the live data actually shows (audited 2026-08-04, 952 mice)

This grounds the plan — some of it differs from first assumptions, so confirm the ⚠ items.

| Facility / Room | Mice | Racks seen (per room) |
|---|---|---|
| **SAF / 40** | 682 | 3371, 2636, 3341, 2640 |
| **CRAF / 157** | 49 | 2909, 3342, 2639, 3344 |
| **CRAF / 57** | 6 | 2909 |
| **EBS / 58** | 10 | `A` |
| **(no location)** | 205 (22%) | — |

**Field completeness:** facility/room/rack ≈ **78%**, rack_col/rack_row ≈ **76%**,
`cage` text ≈ **9%**.

**Distinct `rack_col`:** `A B C D E F G H I J K L M N` — **plus ranges** `A-N`,
`H-L`, `H-N`, `I-K` and junk `0`, `1`.
**Distinct `rack_row`:** `1 … 10` — **plus ranges** `1-5`, `1-10`, `2-3` and junk `-`, `D`.

### What this tells us
1. **Rooms:** SAF 40, **CRAF (57 + 157 — same physical room, merged)** ✅, EBS 58. Rack
   2909 appearing in both CRAF 57 and 157 confirms they're one space.
2. **Rack ID is per-room, not global** (`2909` is in both CRAF rooms) → the map key
   is **(facility, room, rack)**.
3. **Columns run A–N**, not just A–L — the template is bigger than first thought.
4. **Position lives in `rack_col` + `rack_row`**, not the `cage` field. A "cage" on
   the map = the mice sharing one **(rack_col, rack_row)** cell on a rack.
5. **~1 in 5 mice have no location**, and many older rows store a **range** (a whole
   cohort recorded as "cols A–N, rows 1–10" = the entire rack) instead of a precise
   cell. The map needs to handle both, and this becomes real cleanup work (Phase 0).

---

## 2. The physical model

```
Facility (CRAF, SAF, EBS)
└── Room (CRAF 57, CRAF 157, SAF 40, EBS 58)
    └── Rack (e.g. 2909, 3371 …; EBS uses letters like "A")
        └── Side  (front / back — a double-sided rack)
            └── Cell = Column (letter) × Row (number)
                └── Cage (the mice at that cell; may be a cohort)
                    └── Mice
```

- **CRAF and SAF share one rack template** (same physical size). **EBS is not a rack**
  (see below).
- A **cage** is a cell; its contents are the mice whose `(facility, room, rack,
  rack_col, rack_row)` match that cell. The `cage` text field (card number) is
  optional metadata shown in the cell, not the position.

### Rack template (CRAF/SAF) — ✅ confirmed 2026-08-04
- **Two sides, symmetric.** **Front = A–G**, **Back = H–N** (7 columns each side, 14
  total). Side 2 starts at H; both sides have the **same** column and row count.
- **Rows: 1–9.** (Data confirms: standalone row values only reach 9; the stray `1-10` is
  a coarse whole-rack range, not a 10th physical row.)
- ⇒ **14 × 9 = 126** cells per rack (63 per side).

### EBS — ✅ confirmed: not a rack
EBS 58 holds **4 specialized home cages**. Render it as a flat set of **4 cage slots**,
not a column×row grid.

Both templates are stored as **editable config** (see §7) so any tweak stays a one-line change.

---

## 3. Mapping to the existing schema (no migration needed for Phase 1)

Everything the map needs already exists on `mice`:

| Map concept | Column | Notes |
|---|---|---|
| Facility | `facility` | CRAF / SAF / EBS |
| Room | `room` | 57 / 157 / 40 / 58 |
| Rack | `rack` | per-room id |
| Column | `rack_col` | letter A–N (the "H7" import already splits into col H) |
| Row | `rack_row` | number 1–10 |
| Cage card # | `cage` | optional label shown in the cell |
| Contents | the mice matching the above | grouped client-side |

- **Side** is **derived** from the column letter (A–G → front, H–N → back), so **no
  new "side" column** is required.
- Phase 1 is **read-only** and pure front-end → **no schema change, no migration, no
  backup impact.** (A later editing phase reuses the existing `batchMove` writer.)
- Optional later: one `app_config` row `rack_template` (JSON) — additive, still no
  table change.

---

## 4. Geometry — confirmed, plus minor remaining questions

**✅ Confirmed 2026-08-04:**
1. **Rooms:** SAF 40, **CRAF (57 + 157 merged — same room)**, EBS 58.
2. **CRAF/SAF rack:** two symmetric sides — **Front A–G / Back H–N** (7 cols each),
   **rows 1–9** → **126 cells**.
3. **EBS:** not a rack — **4 specialized home cages**, rendered as 4 slots.

**Still open (minor — do NOT block Phase 1):**
4. **Cage card numbers** — does the lab give each cage its own card #, or is a cage just
   its (col, row) cell? (Only affects a small label shown in the cell.)
5. **Color cells by** genotype (cohort) or health status by default? (Easy toggle either way.)
6. **Room floor plan** — do we know where each rack physically stands, or just which racks
   are in the room? (Rack picker to start; true floor map later if we get positions.)
7. **3D** — defer until 2D is in daily use? (Recommended.)

---

## 5. UX & navigation

New top-level tab: **🗺 Map** (or "Rooms"). Breadcrumb-driven drill-down:

**Facility → Room → Rack → cell grid.**

- **Facilities / Rooms view:** cards for CRAF 57, CRAF 157, SAF 40, EBS 58, each with
  a mouse count and a mini occupancy bar. (Derived from live data, so it self-populates.)
- **Room view:** the racks in that room.
  - *If we don't have a floor plan:* a simple grid of **rack tiles** (each tile = a rack,
    shows id + fill %). Recommended start.
  - *If we later get rack positions:* a top-down **floor map** with racks placed to scale.
- **Rack view (the core):** two side-by-side panels (**Front A–G**, **Back H–N**), each a
  **column × row grid**. Each cell:
  - empty → faint outline;
  - occupied → colored by cohort/status, showing cage card # (if any), mouse count, and a
    sex mini-badge (e.g. `2♀1♂`); **breeding cells get the purple 🔬 marker**;
  - **range/imprecise** rows (legacy "A-N / 1-10") → shown in an **"unplaced / whole-rack"
    tray** beside the grid, since they don't pin to one cell.
- **Click a cell →** side panel listing the mice in that cage (reuse the existing mouse
  detail / row rendering); click a mouse → full detail + timeline.

Mobile: grids scroll/pinch-zoom; the two sides stack vertically.

---

## 6. Rendering approach

- **2D (Phase 1–3): SVG or CSS grid, no dependencies.** A rack is 126 cells (2 sides ×
  7 × 9) — trivial to render and re-render. Fits the single-file, no-build, GitHub
  Pages model perfectly. Recommended.
- **3D (Phase 4, optional/stretch):** a "walk into the room" view.
  - Lightweight option: **CSS 3D transforms** for a pseudo-3D room (cheap, no deps).
  - Full option: **Three.js via CDN**, lazy-loaded like the Excel parser already is.
    Heavier; only if the 2D map proves valuable and 3D adds real navigation value.
  - Recommendation: **defer 3D** until 2D is in daily use; 2D delivers ~90% of the value.

---

## 7. Configuration (make the template data-driven)

Add one `app_config` row so dimensions aren't hardcoded:

```json
// key: "rack_template"
{
  "default": { "sides": [["A","B","C","D","E","F","G"], ["H","I","J","K","L","M","N"]], "rows": 9 },
  "EBS":     { "kind": "homecages", "count": 4 }
}
```

- The map reads this; editing it (later, in an admin panel) reshapes the grid with no
  code change. Falls back to a sensible built-in default if the row is absent.
- Room/rack **inventory** is **derived** from `select distinct facility, room, rack`
  to start (self-populating). If we later want to show **empty** racks that have no mice
  yet, we add an explicit inventory config — additive, no schema change.

---

## 8. Data quality — Phase 0 (do first, informs everything)

The map will make gaps obvious, so tackle them up front:

- **205 unplaced mice (22%)** → surface an **"Unplaced" tray** per room/globally, and let
  the user drop them onto cells (drag, or the existing **Batch → Move / location** tool).
- **Range values** (`rack_col` = `A-N`, `rack_row` = `1-10`) → these are whole-rack /
  whole-cohort placeholders. Show them in the tray, not as a single cell, and offer to
  **split a cohort across real cells** (this is exactly the cage-split workflow we already
  built — select mice, set precise col/row/cage).
- **Junk values** (`0`, `1`, `-`, `D`) → flag in a small "needs fixing" list.
- Provide a **read-out** ("Rack 3371: 48 placed, 12 unplaced, 3 imprecise") so cleanup is
  measurable.

No destructive changes — cleanup is done through the existing owner-scoped edit tools.

---

## 9. Phased delivery

| Phase | Deliverable | Writes? | Migration |
|---|---|---|---|
| **0. Audit & cleanup hooks** | Unplaced/imprecise trays + counts; reuse Batch-Move to place mice | uses existing | none |
| **1. 2D rack view (read-only)** | Pick facility→room→rack → two-sided col×row grid, cells colored by cohort/status, click → mice | no | none |
| **2. Room + find** | Room = rack tiles w/ fill %, facility landing, "find this mouse/cohort on the map" highlight, legend + color-by toggle | no | none |
| **3. Edit on the map** | Drag a cage to an empty cell; place unplaced mice; relocate — all via existing `batchMove`, owner-scoped + audited | yes (reuses writer) | none |
| **4. 3D room (stretch)** | Optional walk-in view (CSS-3D first, Three.js only if warranted) | no | none |

Recommended first slice to build after sign-off: **Phase 1 for one rack** (SAF 40 /
3371 — the densest, 227 mice) to validate the grid, colors, and click-through, then
generalize.

---

## 10. Technical constraints, risks, integration

- **Single-file `index.html`, vanilla JS, no build.** 2D via SVG/CSS keeps that intact.
- **Rack ID collisions across rooms** — always key on (facility, room, rack).
- **Two cages in one cell?** Shouldn't happen; if data has it, show a "conflict" badge.
- **Imprecise legacy data** is the main risk to a clean grid — mitigated by the tray (§8).
- **Integrates with what exists:** cell contents reuse mouse-detail rendering; placement
  reuses `batchMove` (owner-scoped, audited); breeding cells reuse the 🔬 model; "find on
  map" can link from search and from requests.
- **Performance/mobile:** fine at this scale; grids scroll on small screens.
- **No migration / no backup impact** through Phase 3.

---

## 11. Status

Geometry is **confirmed** (§4): CRAF/SAF = A–G / H–N × rows 1–9 (126 cells); CRAF 57+157
merged into one room; EBS = 4 home cages. Phase 1 can be built against the real layout;
the remaining questions (§4.4–4.7) are cosmetic and don't block the first slice.

**Next:** build **Phase 1** — the read-only 2D rack grid — starting with **SAF 40 / rack
3371** (227 mice, densest), then the other racks + the EBS home-cage view.
