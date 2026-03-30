"""
Build MDF_Investor_Teaser_Final.pptx
Burnt Red #B84C30 + Dark Slate #3D4F5C | White backgrounds | Arial
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from lxml import etree
from pptx.oxml.ns import qn

# ── Palette ──────────────────────────────────────────────────────────────────
RED          = RGBColor(0xB8, 0x4C, 0x30)
SLATE        = RGBColor(0x3D, 0x4F, 0x5C)
WHITE        = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY   = RGBColor(0xF3, 0xF3, 0xF3)
LIGHT_SLATE  = RGBColor(0xE6, 0xEB, 0xEE)
LIGHT_RED_BG = RGBColor(0xFB, 0xED, 0xE9)
MID_GRAY     = RGBColor(0x8A, 0x93, 0x9C)
MUTED_LIGHT  = RGBColor(0xA8, 0xBA, 0xC5)
DARK_TEXT    = RGBColor(0x1E, 0x1E, 0x1E)
YELLOW       = RGBColor(0xF5, 0xC2, 0x0A)
BORDER_GRAY  = RGBColor(0xD4, 0xD8, 0xDC)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
F = "Arial"
MARGIN = Inches(0.28)
FOOTER_H = Inches(0.36)
FOOTER_TOP = SLIDE_H - FOOTER_H  # Inches(7.14)
HDR_H = Inches(0.875)


# ── Core helpers ─────────────────────────────────────────────────────────────

def rect(slide, l, t, w, h, fill=None, lc=None, lp=0.75):
    shp = slide.shapes.add_shape(1, l, t, w, h)
    if fill:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    else:
        shp.fill.background()
    if lc:
        shp.line.color.rgb = lc
        shp.line.width = Pt(lp)
    else:
        shp.line.fill.background()
    return shp


def rrect(slide, l, t, w, h, fill=None, lc=None, lp=0.75, adj=25000):
    """Rounded rectangle. adj=50000 for pill."""
    shp = slide.shapes.add_shape(5, l, t, w, h)
    if fill:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    else:
        shp.fill.background()
    if lc:
        shp.line.color.rgb = lc
        shp.line.width = Pt(lp)
    else:
        shp.line.fill.background()
    sp = shp._element
    prstGeom = sp.spPr.prstGeom
    avLst = prstGeom.find(qn('a:avLst'))
    if avLst is None:
        avLst = etree.SubElement(prstGeom, qn('a:avLst'))
    for gd in avLst.findall(qn('a:gd')):
        avLst.remove(gd)
    gd_el = etree.SubElement(avLst, qn('a:gd'))
    gd_el.set('name', 'adj')
    gd_el.set('fmla', f'val {adj}')
    return shp


def tb(slide, l, t, w, h, text, sz=10, bold=False, color=DARK_TEXT,
       align=PP_ALIGN.LEFT, italic=False):
    txb = slide.shapes.add_textbox(l, t, w, h)
    txb.word_wrap = True
    tf = txb.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    tf.vertical_anchor = MSO_ANCHOR.TOP
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = F
    run.font.size = Pt(sz)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return txb


def set_text(shp, lines, align=PP_ALIGN.CENTER):
    """Set multi-line text inside a shape, vertically centred."""
    tf = shp.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.clear()
    for i, (txt, sz, bld, itl, col) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        run = p.add_run()
        run.text = txt
        run.font.name = F
        run.font.size = Pt(sz)
        run.font.bold = bld
        run.font.italic = itl
        run.font.color.rgb = col


def col_title(slide, x, y, w, text, text_color=SLATE):
    tb(slide, x, y, w, Inches(0.28), text, sz=11, bold=True, color=text_color)
    rect(slide, x, y + Inches(0.30), Inches(1.0), Pt(2.5), fill=RED)


def bullet_row(slide, x, y, w, text, dot_color=RED, sz=9, pad=Inches(0.15)):
    rect(slide, x + pad + Inches(0.02), y + Inches(0.065),
         Inches(0.06), Inches(0.06), fill=dot_color)
    tb(slide, x + pad + Inches(0.14), y,
       w - pad - Inches(0.20), Inches(0.52),
       text, sz=sz, color=DARK_TEXT)


def footer(slide):
    rect(slide, 0, FOOTER_TOP, SLIDE_W, FOOTER_H, fill=SLATE)
    tb(slide, Inches(0.2), FOOTER_TOP + Inches(0.07),
       SLIDE_W - Inches(0.4), Inches(0.24),
       "partnerships@maddogcleaning.com  ·  Confidential — not an offer to sell securities  ·  March 2026",
       sz=7.5, color=MUTED_LIGHT, align=PP_ALIGN.CENTER)


# ═══════════════════════════════════════════════════════════════════════════════
#  BUILD
# ═══════════════════════════════════════════════════════════════════════════════
prs = Presentation()
prs.slide_width  = SLIDE_W
prs.slide_height = SLIDE_H
blank = prs.slide_layouts[6]


# ═══════════════════════════════════════════════════════════════════════════════
#  SLIDE 1 — THE ASK
# ═══════════════════════════════════════════════════════════════════════════════
s1 = prs.slides.add_slide(blank)
rect(s1, 0, 0, SLIDE_W, SLIDE_H, fill=WHITE)

# ── Header ───────────────────────────────────────────────────────────────────
rect(s1, 0, 0, SLIDE_W, HDR_H, fill=SLATE)
rect(s1, 0, HDR_H, SLIDE_W, Pt(3), fill=RED)

tb(s1, MARGIN, Inches(0.09), Inches(8.0), Inches(0.40),
   "Mad Dog Facility Partners", sz=22, bold=True, color=WHITE)
tb(s1, MARGIN, Inches(0.51), Inches(8.5), Inches(0.26),
   "SDVOSB  ·  Janitorial & Facility Services  ·  IL  ·  WI  ·  AZ  ·  TX",
   sz=10, color=MUTED_LIGHT)

PILL_W = Inches(2.68)
PILL_H = Inches(0.42)
pill = rrect(s1, SLIDE_W - MARGIN - PILL_W, (HDR_H - PILL_H) / 2,
             PILL_W, PILL_H, fill=RED, adj=50000)
set_text(pill, [("Seeking $300K  ·  Convertible Note", 10, True, False, WHITE)])

# ── 4 Stat blocks ────────────────────────────────────────────────────────────
STATS = [
    ("$300K",  "RAISE"),
    ("15%",    "PIK RATE, COMPOUNDING"),
    ("3+2 YR", "MATURITY + EXTENSION"),
    ("$3.5M",  "VALUATION CAP"),
]
SB_TOP = Inches(0.935)
SB_H   = Inches(0.88)
SB_GAP = Inches(0.10)
SB_W   = (SLIDE_W - 2 * MARGIN - 3 * SB_GAP) / 4

for i, (val, lbl) in enumerate(STATS):
    sx = MARGIN + i * (SB_W + SB_GAP)
    rect(s1, sx, SB_TOP, SB_W, SB_H, fill=WHITE, lc=BORDER_GRAY, lp=0.75)
    tb(s1, sx + Inches(0.08), SB_TOP + Inches(0.05), SB_W - Inches(0.16), Inches(0.50),
       val, sz=24, bold=True, color=RED, align=PP_ALIGN.CENTER)
    tb(s1, sx + Inches(0.06), SB_TOP + Inches(0.55), SB_W - Inches(0.12), Inches(0.28),
       lbl, sz=7.5, color=MID_GRAY, align=PP_ALIGN.CENTER)

# ── Two columns ──────────────────────────────────────────────────────────────
COL_TOP = Inches(1.92)
COL_GAP = Inches(0.20)
COL_W   = (SLIDE_W - 2 * MARGIN - COL_GAP) / 2
LX      = MARGIN
RX      = MARGIN + COL_W + COL_GAP

# ── LEFT: Illustrative Returns ───────────────────────────────────────────────
col_title(s1, LX, COL_TOP, COL_W, "Illustrative Returns")

RT = COL_TOP + Inches(0.40)
RH = Inches(0.44)

# Row 1 – light red bg
rect(s1, LX, RT, COL_W, RH, fill=LIGHT_RED_BG)
tb(s1, LX + Inches(0.14), RT + Inches(0.09), Inches(1.6), Inches(0.28),
   "Year 3 exit", sz=10, bold=True, color=RED)
tb(s1, LX + COL_W - Inches(3.25), RT + Inches(0.09), Inches(3.10), Inches(0.28),
   "~$735K returned  ·  ~2.5x MOIC", sz=10, bold=True, color=RED, align=PP_ALIGN.RIGHT)

# Row 2 – slate
R2T = RT + RH + Inches(0.05)
rect(s1, LX, R2T, COL_W, RH, fill=SLATE)
tb(s1, LX + Inches(0.14), R2T + Inches(0.09), Inches(1.6), Inches(0.28),
   "Year 5 exit", sz=10, bold=True, color=WHITE)
tb(s1, LX + COL_W - Inches(3.25), R2T + Inches(0.09), Inches(3.10), Inches(0.28),
   "~$1.05M returned  ·  ~3.5x MOIC", sz=10, bold=True, color=WHITE, align=PP_ALIGN.RIGHT)

# Footnote
FN_TOP = R2T + RH + Inches(0.10)
tb(s1, LX, FN_TOP, COL_W, Inches(0.60),
   "Investor owns 8.6% equity at cap ($300K / $3.5M). Yr 5 assumes $1M EBITDA at 5x valuation. "
   "Paid out via SBA recap — founder retains 100% ownership.",
   sz=7.5, color=MID_GRAY, italic=True)

# 2×2 stat grid (light slate bg)
GRID_TOP = FN_TOP + Inches(0.72)
GRID_ITEMS = [
    ("$300K",   "Principal"),
    ("15% PIK", "Annual compounding"),
    ("3 yr",    "Maturity"),
    ("+2 yr",   "Investor extension option"),
]
GW  = (COL_W - Inches(0.08)) / 2
GH  = Inches(0.74)
GG  = Inches(0.08)
for idx, (val, lbl) in enumerate(GRID_ITEMS):
    ci = idx % 2
    ri = idx // 2
    gx = LX + ci * (GW + GG)
    gy = GRID_TOP + ri * (GH + GG)
    rect(s1, gx, gy, GW, GH, fill=LIGHT_SLATE)
    tb(s1, gx + Inches(0.06), gy + Inches(0.08), GW - Inches(0.12), Inches(0.36),
       val, sz=15, bold=True, color=RED, align=PP_ALIGN.CENTER)
    tb(s1, gx + Inches(0.06), gy + Inches(0.43), GW - Inches(0.12), Inches(0.28),
       lbl, sz=7.5, color=MID_GRAY, align=PP_ALIGN.CENTER)

# ── RIGHT: Use of Proceeds ───────────────────────────────────────────────────
col_title(s1, RX, COL_TOP, COL_W, "Use of Proceeds")

UOP = [
    ("SDR hire Year 1 (base + ramp)", "$110K", False),
    ("M&A dry powder",                "$130K", False),
    ("Working capital cushion",       "$40K",  False),
    ("Founder comp increase",         "$20K",  False),
    ("Total",                         "$300K", True),
]
UT = COL_TOP + Inches(0.40)
UH = Inches(0.40)
for k, (item, amt, total) in enumerate(UOP):
    uy = UT + k * UH
    row_fill = LIGHT_GRAY if k % 2 == 0 else WHITE
    if total:
        row_fill = WHITE
        rect(s1, RX, uy, COL_W, Pt(1.5), fill=RED)
    rect(s1, RX, uy, COL_W, UH, fill=row_fill)
    ic = RED if total else DARK_TEXT
    tb(s1, RX + Inches(0.12), uy + Inches(0.09), COL_W - Inches(0.82), UH - Inches(0.12),
       item, sz=9.5, bold=total, color=ic)
    tb(s1, RX + COL_W - Inches(0.72), uy + Inches(0.09), Inches(0.62), UH - Inches(0.12),
       amt, sz=9.5, bold=total, color=ic, align=PP_ALIGN.RIGHT)

# 5-year target box
TGT_TOP = UT + len(UOP) * UH + Inches(0.20)
TGT_H   = Inches(1.36)
rect(s1, RX, TGT_TOP, COL_W, TGT_H, fill=LIGHT_SLATE, lc=BORDER_GRAY, lp=0.75)
tb(s1, RX + Inches(0.14), TGT_TOP + Inches(0.10), Inches(1.4), Inches(0.22),
   "5-year target", sz=8.5, bold=True, color=SLATE)
for j, line in enumerate([
    "$5–6M revenue  ·  $1M EBITDA",
    "Organic growth + M&A platform",
    "SBA recap at maturity — clean investor exit",
]):
    tb(s1, RX + Inches(0.14), TGT_TOP + Inches(0.36) + j * Inches(0.28),
       COL_W - Inches(0.22), Inches(0.28), line, sz=9, color=SLATE)

footer(s1)


# ═══════════════════════════════════════════════════════════════════════════════
#  SLIDE 2 — THE STORY AND OPPORTUNITY
# ═══════════════════════════════════════════════════════════════════════════════
s2 = prs.slides.add_slide(blank)
rect(s2, 0, 0, SLIDE_W, SLIDE_H, fill=WHITE)

# ── Header ───────────────────────────────────────────────────────────────────
rect(s2, 0, 0, SLIDE_W, HDR_H, fill=SLATE)
rect(s2, 0, HDR_H, SLIDE_W, Pt(3), fill=RED)
tb(s2, MARGIN, Inches(0.09), Inches(9.5), Inches(0.40),
   "The story and the opportunity", sz=20, bold=True, color=WHITE)
tb(s2, MARGIN, Inches(0.52), Inches(9.5), Inches(0.26),
   "Where we've been  ·  Where we are  ·  Where we're going",
   sz=10, color=MUTED_LIGHT)

# ── 3 Hero stats ─────────────────────────────────────────────────────────────
HERO = [
    ("$693K",   "2025 REVENUE (+19% VS 2024)"),
    ("+$170K",  "ARR ADDED IN 4 MONTHS, PART-TIME"),
    ("~$50K",   "CURRENT MRR RUN RATE"),
]
HS_TOP = Inches(0.935)
HS_H   = Inches(0.88)
HS_GAP = Inches(0.12)
HS_W   = (SLIDE_W - 2 * MARGIN - 2 * HS_GAP) / 3

for i, (val, lbl) in enumerate(HERO):
    hx = MARGIN + i * (HS_W + HS_GAP)
    rect(s2, hx, HS_TOP, HS_W, HS_H, fill=WHITE, lc=BORDER_GRAY, lp=0.75)
    tb(s2, hx + Inches(0.08), HS_TOP + Inches(0.05), HS_W - Inches(0.16), Inches(0.48),
       val, sz=26, bold=True, color=RED, align=PP_ALIGN.CENTER)
    tb(s2, hx + Inches(0.06), HS_TOP + Inches(0.55), HS_W - Inches(0.12), Inches(0.28),
       lbl, sz=8, color=MID_GRAY, align=PP_ALIGN.CENTER)

# ── 3-column journey ─────────────────────────────────────────────────────────
JT  = Inches(1.91)
JH  = FOOTER_TOP - Inches(0.06) - JT
JM  = Inches(0.20)
JG  = Inches(0.04)
JW  = (SLIDE_W - 2 * JM - 2 * JG) / 3
JP  = Inches(0.15)

C1X = JM
C2X = JM + JW + JG
C3X = JM + 2 * JW + 2 * JG

# Column backgrounds
rect(s2, C1X, JT, JW, JH, fill=LIGHT_GRAY)
rect(s2, C2X, JT, JW, JH, fill=WHITE, lc=BORDER_GRAY, lp=0.5)
rect(s2, C3X, JT, JW, JH, fill=LIGHT_SLATE)

# Separator lines
rect(s2, C2X - JG, JT, JG, JH, fill=BORDER_GRAY)
rect(s2, C3X - JG, JT, JG, JH, fill=BORDER_GRAY)

def jheader(slide, x, y, w, text, tc):
    tb(slide, x + JP, y + Inches(0.10), w - 2 * JP, Inches(0.24),
       text, sz=8, bold=True, color=tc)
    rect(slide, x + JP, y + Inches(0.35), Inches(0.7), Pt(2), fill=RED)

jheader(s2, C1X, JT, JW, "WHERE WE'VE BEEN", MID_GRAY)
jheader(s2, C2X, JT, JW, "WHERE WE ARE", SLATE)
jheader(s2, C3X, JT, JW, "WHERE WE'RE GOING POST-RAISE", SLATE)

# ── Col 1 ────────────────────────────────────────────────────────────────────
C1_TOP = JT + Inches(0.44)
C1_BULLETS = [
    "Acquired at $425K revenue in 2024",
    "Grew to $693K by end of 2025 — +19% organic",
    "Lost largest customer Sept 2025 — $336K ARR overnight",
    "Revenue dropped nearly 50% in one event",
    "Rebuilt $170K ARR in under 4 months, fractional effort, zero dedicated SDR",
]
for j, b in enumerate(C1_BULLETS):
    bullet_row(s2, C1X, C1_TOP + j * Inches(0.57), JW, b, dot_color=RED, pad=JP)

# Yellow left-border callout
CY = C1_TOP + len(C1_BULLETS) * Inches(0.57) + Inches(0.08)
rect(s2, C1X + JP, CY, JW - 2 * JP, Inches(0.50), fill=WHITE, lc=BORDER_GRAY, lp=0.5)
rect(s2, C1X + JP, CY, Pt(4), Inches(0.50), fill=YELLOW)
tb(s2, C1X + JP + Inches(0.14), CY + Inches(0.11),
   JW - 2 * JP - Inches(0.18), Inches(0.32),
   "Proof of concept on a skeleton crew.", sz=9, italic=True, color=SLATE)

# ── Col 2 ────────────────────────────────────────────────────────────────────
C2_TOP = JT + Inches(0.44)
C2_BULLETS = [
    "~$50K MRR, recovery trajectory",
    "$134K net income in 2025 (19% margin)",
    "Growing $10–15K MRR per quarter on part-time sales",
    "Active acquisition in late-stage diligence — meaningful EBITDA accretion at close",
    "SDVOSB set-aside certifications across 4 states",
    "GovCon RFP team actively building pipeline",
]
for j, b in enumerate(C2_BULLETS):
    bullet_row(s2, C2X, C2_TOP + j * Inches(0.57), JW, b, dot_color=SLATE, pad=JP)

# ── Col 3 ────────────────────────────────────────────────────────────────────
C3_TOP  = JT + Inches(0.44)
PH      = Inches(0.54)   # pill height
PG      = Inches(0.07)   # gap between pills

# Red pills
RED_PILLS = [
    "SDR 1 (this raise): $50–75K MRR growth per quarter",
    "SDR 2 (yr 1–2, self-funded): +$50–75K+ MRR/qtr",
]
for j, pt in enumerate(RED_PILLS):
    py = C3_TOP + j * (PH + PG)
    p = rrect(s2, C3X + JP, py, JW - 2 * JP, PH, fill=RED, adj=30000)
    set_text(p, [(pt, 8.5, True, False, WHITE)])

# Slate pill
SP_Y = C3_TOP + 2 * (PH + PG)
sp = rrect(s2, C3X + JP, SP_Y, JW - 2 * JP, PH, fill=SLATE, adj=30000)
set_text(sp, [("GovCon RFP team: $150K+ ARR in set-aside contracts — sticky, recurring",
               8.5, True, False, WHITE)])

# Regular bullets
C3_B2_TOP = SP_Y + PH + Inches(0.14)
C3_BULLETS_2 = [
    "Active acquisition closes, adding EBITDA to platform",
    "Infrastructure scaled to handle and retain growth volume",
    "Path to $1M EBITDA in 5 years, organic + M&A",
]
for j, b in enumerate(C3_BULLETS_2):
    bullet_row(s2, C3X, C3_B2_TOP + j * Inches(0.55), JW, b, dot_color=RED, pad=JP)

footer(s2)

# ── Save ─────────────────────────────────────────────────────────────────────
out = "/home/user/operations/MDF_Investor_Teaser_Final.pptx"
prs.save(out)
print(f"Saved: {out}")
