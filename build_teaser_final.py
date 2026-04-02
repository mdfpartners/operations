"""
MDF_Investor_Teaser_Final.pptx — 3 slides
Red #B84C30 + Slate #3D4F5C | White backgrounds | Arial
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from lxml import etree
from pptx.oxml.ns import qn

# ── Palette ───────────────────────────────────────────────────────────────────
RED          = RGBColor(0xB8, 0x4C, 0x30)
SLATE        = RGBColor(0x3D, 0x4F, 0x5C)
SLATE_DARK   = RGBColor(0x2C, 0x3A, 0x44)
SLATE_MID    = RGBColor(0x5E, 0x72, 0x80)
WHITE        = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY   = RGBColor(0xF3, 0xF3, 0xF3)
LIGHT_SLATE  = RGBColor(0xE6, 0xEB, 0xEE)
LIGHT_RED_BG = RGBColor(0xFB, 0xED, 0xE9)
LIGHT_GREEN  = RGBColor(0xE8, 0xF5, 0xE9)
GREEN        = RGBColor(0x2E, 0x7D, 0x32)
MID_GRAY     = RGBColor(0x8A, 0x93, 0x9C)
TAG_GRAY     = RGBColor(0x94, 0x9E, 0xA8)
MUTED_LIGHT  = RGBColor(0xA8, 0xBA, 0xC5)
DARK_TEXT    = RGBColor(0x1E, 0x1E, 0x1E)
YELLOW       = RGBColor(0xF5, 0xC2, 0x0A)
BORDER_GRAY  = RGBColor(0xD4, 0xD8, 0xDC)
RED_MUTED    = RGBColor(0xF5, 0xC5, 0xB8)

SLIDE_W    = Inches(13.333)
SLIDE_H    = Inches(7.5)
F          = "Arial"
MARGIN     = Inches(0.28)
HDR_H      = Inches(0.875)
FOOTER_H   = Inches(0.36)
FOOTER_TOP = SLIDE_H - FOOTER_H          # Inches(7.14)

# ── Core helpers ──────────────────────────────────────────────────────────────

def rect(slide, l, t, w, h, fill=None, lc=None, lp=0.75):
    shp = slide.shapes.add_shape(1, l, t, w, h)
    if fill:
        shp.fill.solid(); shp.fill.fore_color.rgb = fill
    else:
        shp.fill.background()
    if lc:
        shp.line.color.rgb = lc; shp.line.width = Pt(lp)
    else:
        shp.line.fill.background()
    return shp


def rrect(slide, l, t, w, h, fill=None, lc=None, lp=0.75, adj=25000):
    shp = slide.shapes.add_shape(5, l, t, w, h)
    if fill:
        shp.fill.solid(); shp.fill.fore_color.rgb = fill
    else:
        shp.fill.background()
    if lc:
        shp.line.color.rgb = lc; shp.line.width = Pt(lp)
    else:
        shp.line.fill.background()
    sp = shp._element
    pG = sp.spPr.prstGeom
    aL = pG.find(qn('a:avLst'))
    if aL is None:
        aL = etree.SubElement(pG, qn('a:avLst'))
    for g in aL.findall(qn('a:gd')):
        aL.remove(g)
    gd = etree.SubElement(aL, qn('a:gd'))
    gd.set('name', 'adj'); gd.set('fmla', f'val {adj}')
    return shp


def tb(slide, l, t, w, h, text, sz=10, bold=False, color=DARK_TEXT,
       align=PP_ALIGN.LEFT, italic=False):
    txb = slide.shapes.add_textbox(l, t, w, h)
    txb.word_wrap = True
    tf = txb.text_frame
    tf.word_wrap = True; tf.auto_size = None
    tf.vertical_anchor = MSO_ANCHOR.TOP
    p = tf.paragraphs[0]; p.alignment = align
    run = p.add_run()
    run.text = text; run.font.name = F
    run.font.size = Pt(sz); run.font.bold = bold
    run.font.italic = italic; run.font.color.rgb = color
    return txb


def set_text(shp, lines, align=PP_ALIGN.CENTER):
    tf = shp.text_frame
    tf.word_wrap = True; tf.auto_size = None
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.clear()
    for i, (txt, sz, bld, itl, col) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        run = p.add_run()
        run.text = txt; run.font.name = F
        run.font.size = Pt(sz); run.font.bold = bld
        run.font.italic = itl; run.font.color.rgb = col


def col_title(slide, x, y, w, text, color=SLATE):
    tb(slide, x, y, w, Inches(0.28), text, sz=10, bold=True, color=color)
    rect(slide, x, y + Inches(0.30), Inches(1.0), Pt(2.5), fill=RED)


def badge(slide, x, y, text, bg, tc=WHITE, w=Inches(0.55), h=Inches(0.17)):
    shp = rrect(slide, x, y, w, h, fill=bg, adj=35000)
    set_text(shp, [(text, 6.5, True, False, tc)])


def hdr(slide, title, sub=None, badge_text=None, badge_w=Inches(2.75)):
    rect(slide, 0, 0, SLIDE_W, HDR_H, fill=SLATE)
    rect(slide, 0, HDR_H, SLIDE_W, Pt(3), fill=RED)
    tb(slide, MARGIN, Inches(0.09), Inches(9.0), Inches(0.40),
       title, sz=16, bold=True, color=WHITE)
    if sub:
        tb(slide, MARGIN, Inches(0.52), Inches(9.5), Inches(0.26),
           sub, sz=9, color=MUTED_LIGHT)
    if badge_text:
        BH = Inches(0.38)
        pill = rrect(slide, SLIDE_W - MARGIN - badge_w,
                     (HDR_H - BH) / 2, badge_w, BH, fill=RED, adj=50000)
        set_text(pill, [(badge_text, 9, True, False, WHITE)])


def footer_bar(slide, text, sz=7):
    rect(slide, 0, FOOTER_TOP, SLIDE_W, FOOTER_H, fill=SLATE)
    tb(slide, Inches(0.2), FOOTER_TOP + Inches(0.07),
       SLIDE_W - Inches(0.4), FOOTER_H - Inches(0.09),
       text, sz=sz, color=MUTED_LIGHT, align=PP_ALIGN.CENTER)


def bullet_row(slide, x, y, w, text, dot=RED, sz=9, pad=Inches(0.15)):
    rect(slide, x + pad + Inches(0.02), y + Inches(0.065),
         Inches(0.06), Inches(0.06), fill=dot)
    tb(slide, x + pad + Inches(0.14), y,
       w - pad - Inches(0.20), Inches(0.52), text, sz=sz, color=DARK_TEXT)


# ═══════════════════════════════════════════════════════════════════════════════
prs = Presentation()
prs.slide_width  = SLIDE_W
prs.slide_height = SLIDE_H
blank = prs.slide_layouts[6]

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — THE ASK
# ═══════════════════════════════════════════════════════════════════════════════
s1 = prs.slides.add_slide(blank)
rect(s1, 0, 0, SLIDE_W, SLIDE_H, fill=WHITE)

hdr(s1, "Mad Dog Facility Partners",
    "SDVOSB  \u00b7  Janitorial & Facility Services  \u00b7  IL  \u00b7  WI  \u00b7  AZ  \u00b7  TX",
    "Seeking $350K  \u00b7  Convertible Note")

# ── 4 stat blocks ─────────────────────────────────────────────────────────────
STATS_1 = [
    ("$350K",        "RAISE"),
    ("5% PIK",       "ANNUAL COMPOUNDING"),
    ("8.75% EQUITY", "AT $4M CAP"),
    ("4 YR",         "SINGLE LIQUIDITY EVENT"),
]
SB_TOP = Inches(0.935)
SB_H   = Inches(0.88)
SB_GAP = Inches(0.10)
SB_W   = (SLIDE_W - 2 * MARGIN - 3 * SB_GAP) / 4
for i, (val, lbl) in enumerate(STATS_1):
    sx = MARGIN + i * (SB_W + SB_GAP)
    rect(s1, sx, SB_TOP, SB_W, SB_H, fill=WHITE, lc=BORDER_GRAY, lp=0.75)
    tb(s1, sx + Inches(0.06), SB_TOP + Inches(0.05), SB_W - Inches(0.12), Inches(0.50),
       val, sz=20, bold=True, color=RED, align=PP_ALIGN.CENTER)
    tb(s1, sx + Inches(0.06), SB_TOP + Inches(0.56), SB_W - Inches(0.12), Inches(0.28),
       lbl, sz=7.5, color=MID_GRAY, align=PP_ALIGN.CENTER)

# ── Two columns ───────────────────────────────────────────────────────────────
COL_TOP = Inches(1.90)
COL_GAP = Inches(0.20)
COL_W   = (SLIDE_W - 2 * MARGIN - COL_GAP) / 2   # ~6.287"
LX      = MARGIN
RX      = MARGIN + COL_W + COL_GAP

# ── LEFT: Illustrative Returns ─────────────────────────────────────────────────
col_title(s1, LX, COL_TOP, COL_W, "ILLUSTRATIVE RETURNS")

# Sensitivity table — column widths summing to COL_W
TC = [Inches(x) for x in [1.80, 0.88, 0.85, 0.88, 0.67, 1.207]]
# sum = 6.287 ≈ COL_W ✓

TABLE_TOP = COL_TOP + Inches(0.38)
TH = Inches(0.33)   # header row height
DR = Inches(0.31)   # data row height

# Header row
HDR_COLS = ["Valuation at Year 4", "Principal + PIK",
            "Equity Value", "Total Payout", "MOIC", "4-yr IRR"]
rect(s1, LX, TABLE_TOP, COL_W, TH, fill=SLATE)
cx = LX
for j, (lbl, cw) in enumerate(zip(HDR_COLS, TC)):
    algn = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.RIGHT
    offset = Inches(0.08) if j == 0 else Inches(0.04)
    tb(s1, cx + offset, TABLE_TOP + Inches(0.06),
       cw - Inches(0.10), TH - Inches(0.06),
       lbl, sz=7.5, bold=True, color=WHITE, align=algn)
    cx += cw

# Data rows
# (val, tag_txt, tag_bg, row_bg, text_col, bold, pik, equity, total, moic, irr)
SENS = [
    ("$2.5M", "downside", TAG_GRAY,     LIGHT_GRAY,   DARK_TEXT, False,
     "$447K", "$219K", "$666K", "1.90x", "17.4%"),
    ("$3.0M", None,       None,          WHITE,         DARK_TEXT, False,
     "$447K", "$263K", "$710K", "2.03x", "19.4%"),
    ("$3.5M", None,       None,          LIGHT_GRAY,   DARK_TEXT, False,
     "$447K", "$306K", "$753K", "2.15x", "21.1%"),
    ("$4.0M", "cap",      RED,           LIGHT_RED_BG, RED,        True,
     "$447K", "$350K", "$797K", "2.28x", "22.8%"),
    ("$4.5M", None,       None,          LIGHT_GRAY,   DARK_TEXT, False,
     "$447K", "$394K", "$841K", "2.40x", "24.4%"),
    ("$5.0M", "target",   SLATE,         SLATE,        WHITE,      True,
     "$447K", "$438K", "$885K", "2.53x", "26.0%"),
    ("$5.5M", None,       None,          WHITE,         DARK_TEXT, False,
     "$447K", "$481K", "$928K", "2.65x", "27.5%"),
]
for k, (val, tag_txt, tag_bg, row_bg, tc_col, bold_row,
        pik, eq, tot, moic, irr) in enumerate(SENS):
    ry = TABLE_TOP + TH + k * DR
    rect(s1, LX, ry, COL_W, DR, fill=row_bg)
    # value text
    tb(s1, LX + Inches(0.08), ry + Inches(0.05), Inches(0.52), DR - Inches(0.06),
       val, sz=9, bold=bold_row, color=tc_col)
    # optional tag badge
    if tag_txt:
        badge(s1, LX + Inches(0.63), ry + (DR - Inches(0.17)) / 2,
              tag_txt, tag_bg)
    # numeric columns (right-aligned)
    row_vals = [pik, eq, tot, moic, irr]
    cx2 = LX + TC[0]
    for dval, cw in zip(row_vals, TC[1:]):
        tb(s1, cx2 + Inches(0.04), ry + Inches(0.05),
           cw - Inches(0.08), DR - Inches(0.06),
           dval, sz=9, bold=bold_row, color=tc_col, align=PP_ALIGN.RIGHT)
        cx2 += cw

# Footnote
FN_Y = TABLE_TOP + TH + 7 * DR + Inches(0.08)
tb(s1, LX, FN_Y, COL_W, Inches(0.50),
   "PIK accrual: $350K \u00d7 (1.05)\u2074 = $447K.  "
   "Equity: 8.75% \u00d7 exit valuation ($350K / $4M cap).  "
   "IRR: (total / $350K)^(0.25) \u2212 1.",
   sz=7, color=MID_GRAY, italic=True)

# Slate bottom banner
BNR_Y = FN_Y + Inches(0.56)
BNR_H = Inches(0.72)
rect(s1, LX, BNR_Y, COL_W, BNR_H, fill=SLATE)
tb(s1, LX + Inches(0.12), BNR_Y + Inches(0.08),
   COL_W * 0.52, BNR_H - Inches(0.12),
   "~22.8% IRR at valuation cap  \u00b7  "
   "Private equity-level returns on a cash-flowing business",
   sz=9, bold=True, color=WHITE)
tb(s1, LX + COL_W * 0.56, BNR_Y + Inches(0.08),
   COL_W * 0.42 - Inches(0.10), BNR_H - Inches(0.12),
   "Principal + PIK of $447K fixed regardless of exit valuation. "
   "Equity scales with performance. SBA recap at year 4 \u2014 founder retains 100% ownership.",
   sz=7.5, color=MUTED_LIGHT, italic=True)

# ── RIGHT: Use of Proceeds ─────────────────────────────────────────────────────
col_title(s1, RX, COL_TOP, COL_W, "USE OF PROCEEDS")

UOP = [
    ("SDR 1 \u2014 Year 1 (base + ramp)",          "$50K",  False),
    ("SDR 2 \u2014 Year 2 reserve",                 "$25K",  False),
    ("Project manager",                              "$30K",  False),
    ("Offshore bookkeeper",                          "$15K",  False),
    ("GovCon analyst",                               "$12K",  False),
    ("Office manager (offshore, part-time)",         "$10K",  False),
    ("Working capital cushion",                      "$30K",  False),
    ("Founder comp increase",                        "$18K",  False),
    ("Contingency buffer",                           "$10K",  False),
    ("Total",                                        "$200K", True),
]
UT = COL_TOP + Inches(0.38)
UH = Inches(0.30)
for k, (item, amt, total) in enumerate(UOP):
    uy = UT + k * UH
    row_fill = LIGHT_GRAY if k % 2 == 0 else WHITE
    if total:
        row_fill = WHITE
        rect(s1, RX, uy, COL_W, Pt(1.5), fill=RED)
    rect(s1, RX, uy, COL_W, UH, fill=row_fill)
    ic = RED if total else DARK_TEXT
    tb(s1, RX + Inches(0.10), uy + Inches(0.06),
       COL_W - Inches(0.80), UH - Inches(0.08),
       item, sz=8.5, bold=total, color=ic)
    tb(s1, RX + COL_W - Inches(0.70), uy + Inches(0.06),
       Inches(0.62), UH - Inches(0.08),
       amt, sz=8.5, bold=total, color=ic, align=PP_ALIGN.RIGHT)

# 5-year target box
TGT_Y = UT + len(UOP) * UH + Inches(0.14)
TGT_H = Inches(1.10)
rect(s1, RX, TGT_Y, COL_W, TGT_H, fill=LIGHT_SLATE, lc=BORDER_GRAY, lp=0.75)
tb(s1, RX + Inches(0.12), TGT_Y + Inches(0.09),
   Inches(1.2), Inches(0.22),
   "5-year target", sz=8.5, bold=True, color=SLATE)
for j, line in enumerate([
    "$5\u20136M revenue  \u00b7  $1M EBITDA",
    "Organic growth + M&A platform",
    "SBA recap at maturity \u2014 clean investor exit",
]):
    tb(s1, RX + Inches(0.12), TGT_Y + Inches(0.34) + j * Inches(0.24),
       COL_W - Inches(0.22), Inches(0.24), line, sz=9, color=SLATE)

footer_bar(s1,
    "partnerships@maddogcleaning.com  \u00b7  "
    "Confidential \u2014 not an offer to sell securities  \u00b7  March 2026")


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — THE STORY AND OPPORTUNITY
# ═══════════════════════════════════════════════════════════════════════════════
s2 = prs.slides.add_slide(blank)
rect(s2, 0, 0, SLIDE_W, SLIDE_H, fill=WHITE)

hdr(s2, "The story and the opportunity",
    "Where we've been  \u00b7  Where we are  \u00b7  Where we're going")

# Hero stats
HERO = [
    ("$693K",   "2025 REVENUE (+19% VS 2024)"),
    ("+$170K",  "ARR ADDED IN 4 MONTHS, PART-TIME"),
    ("\u007e$50K",  "CURRENT MRR RUN RATE"),
]
HS_TOP = Inches(0.935)
HS_H   = Inches(0.88)
HS_GAP = Inches(0.12)
HS_W   = (SLIDE_W - 2 * MARGIN - 2 * HS_GAP) / 3
for i, (val, lbl) in enumerate(HERO):
    hx = MARGIN + i * (HS_W + HS_GAP)
    rect(s2, hx, HS_TOP, HS_W, HS_H, fill=WHITE, lc=BORDER_GRAY, lp=0.75)
    tb(s2, hx + Inches(0.08), HS_TOP + Inches(0.05),
       HS_W - Inches(0.16), Inches(0.48),
       val, sz=26, bold=True, color=RED, align=PP_ALIGN.CENTER)
    tb(s2, hx + Inches(0.06), HS_TOP + Inches(0.55),
       HS_W - Inches(0.12), Inches(0.28),
       lbl, sz=8, color=MID_GRAY, align=PP_ALIGN.CENTER)

# 3-column journey
JT  = Inches(1.91)
JH  = FOOTER_TOP - Inches(0.06) - JT
JM  = Inches(0.20)
JG  = Inches(0.04)
JW  = (SLIDE_W - 2 * JM - 2 * JG) / 3
JP  = Inches(0.15)
C1X = JM
C2X = JM + JW + JG
C3X = JM + 2 * JW + 2 * JG

rect(s2, C1X, JT, JW, JH, fill=LIGHT_GRAY)
rect(s2, C2X, JT, JW, JH, fill=WHITE, lc=BORDER_GRAY, lp=0.5)
rect(s2, C3X, JT, JW, JH, fill=LIGHT_SLATE)
rect(s2, C2X - JG, JT, JG, JH, fill=BORDER_GRAY)
rect(s2, C3X - JG, JT, JG, JH, fill=BORDER_GRAY)

def jheader(slide, x, y, w, text, tc):
    tb(slide, x + JP, y + Inches(0.10), w - 2 * JP, Inches(0.24),
       text, sz=8, bold=True, color=tc)
    rect(slide, x + JP, y + Inches(0.35), Inches(0.7), Pt(2), fill=RED)

jheader(s2, C1X, JT, JW, "WHERE WE'VE BEEN", MID_GRAY)
jheader(s2, C2X, JT, JW, "WHERE WE ARE", SLATE)
jheader(s2, C3X, JT, JW, "WHERE WE'RE GOING POST-RAISE", SLATE)

# Col 1
C1_TOP = JT + Inches(0.44)
for j, b in enumerate([
    "Acquired at $425K revenue in 2024",
    "Grew to $693K by end of 2025 \u2014 +19% organic",
    "Lost largest customer Sept 2025 \u2014 $336K ARR overnight",
    "Revenue dropped nearly 50% in one event",
    "Rebuilt $170K ARR in under 4 months, fractional effort, zero dedicated SDR",
]):
    bullet_row(s2, C1X, C1_TOP + j * Inches(0.57), JW, b, dot=RED, pad=JP)

CY = C1_TOP + 5 * Inches(0.57) + Inches(0.08)
rect(s2, C1X + JP, CY, JW - 2 * JP, Inches(0.50),
     fill=WHITE, lc=BORDER_GRAY, lp=0.5)
rect(s2, C1X + JP, CY, Pt(4), Inches(0.50), fill=YELLOW)
tb(s2, C1X + JP + Inches(0.14), CY + Inches(0.11),
   JW - 2 * JP - Inches(0.18), Inches(0.32),
   "Proof of concept on a skeleton crew.", sz=9, italic=True, color=SLATE)

# Col 2
C2_TOP = JT + Inches(0.44)
for j, b in enumerate([
    "\u007e$50K MRR, recovery trajectory",
    "$134K net income in 2025 (19% margin)",
    "Growing $10\u201315K MRR per quarter on part-time sales",
    "Active acquisition in late-stage diligence \u2014 meaningful EBITDA accretion at close",
    "SDVOSB set-aside certifications across 4 states",
    "GovCon RFP team actively building pipeline",
]):
    bullet_row(s2, C2X, C2_TOP + j * Inches(0.57), JW, b, dot=SLATE, pad=JP)

# Col 3 — pills then bullets
C3_TOP = JT + Inches(0.44)
PH = Inches(0.54)
PG = Inches(0.07)
for j, pt in enumerate([
    "SDR 1 (raise funded): $50\u201375K MRR growth per quarter",
    "SDR 2 (raise funded): additional $50\u201375K+ MRR/qtr",
]):
    py = C3_TOP + j * (PH + PG)
    p = rrect(s2, C3X + JP, py, JW - 2 * JP, PH, fill=RED, adj=30000)
    set_text(p, [(pt, 8.5, True, False, WHITE)])

SP_Y = C3_TOP + 2 * (PH + PG)
sp = rrect(s2, C3X + JP, SP_Y, JW - 2 * JP, PH, fill=SLATE, adj=30000)
set_text(sp, [("GovCon RFP team: $150K+ ARR in set-aside contracts \u2014 sticky, recurring",
               8.5, True, False, WHITE)])

C3_B2_TOP = SP_Y + PH + Inches(0.14)
for j, b in enumerate([
    "SDR 3 added yr 3, ops-cash funded",
    "Active acquisition closes mid yr 3 \u2014 EBITDA accretive at NewCo level",
    "Infrastructure scaled to handle and retain volume",
    "Path to $1M EBITDA in 4\u20135 years, organic + M&A",
]):
    bullet_row(s2, C3X, C3_B2_TOP + j * Inches(0.52), JW, b, dot=RED, pad=JP)

footer_bar(s2,
    "partnerships@maddogcleaning.com  \u00b7  "
    "Confidential \u2014 not an offer to sell securities  \u00b7  March 2026")


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — EBITDA BRIDGE
# ═══════════════════════════════════════════════════════════════════════════════
s3 = prs.slides.add_slide(blank)
rect(s3, 0, 0, SLIDE_W, SLIDE_H, fill=WHITE)

hdr(s3,
    "4\u20135 year path to $1M+ EBITDA",
    "Organic base case (3 SDR + GovCon compounding) + opportunistic acquisition")

# Small white/muted disclaimer badge on the right
DISC_W = Inches(3.30)
DISC_H = Inches(0.34)
disc = rrect(s3, SLIDE_W - MARGIN - DISC_W, (HDR_H - DISC_H) / 2,
             DISC_W, DISC_H, fill=MUTED_LIGHT, adj=50000)
set_text(disc, [("Illustrative \u2014 not a guarantee of performance",
                 7.5, False, True, SLATE)])

# ── Legend row ────────────────────────────────────────────────────────────────
LEGEND = [
    (SLATE,     "Current base"),
    (RED,       "SDR channel (raise funded)"),
    (MID_GRAY,  "SDR 3 (ops funded)"),
    (SLATE_MID, "GovCon / set-aside"),
    (GREEN,     "Opportunistic acquisition"),
]
LGD_Y  = Inches(0.93)
LGD_H  = Inches(0.28)
SW     = Inches(0.13)
# Pre-computed item widths to distribute evenly
ITEM_WIDTHS = [Inches(x) for x in [1.80, 2.35, 2.00, 2.00, 2.20]]
lgd_x = MARGIN
for (dot_col, lbl), item_w in zip(LEGEND, ITEM_WIDTHS):
    rect(s3, lgd_x, LGD_Y + (LGD_H - SW) / 2, SW, SW, fill=dot_col)
    tb(s3, lgd_x + SW + Inches(0.06), LGD_Y, item_w - SW - Inches(0.08), LGD_H,
       lbl, sz=8, color=MID_GRAY)
    lgd_x += item_w

# ── EBITDA table ──────────────────────────────────────────────────────────────
TM     = Inches(0.22)          # table margin
TBL_W  = SLIDE_W - 2 * TM     # ~12.893"
DRV_W  = Inches(2.70)
DAT_W  = (TBL_W - DRV_W) / 6  # ~1.699" per data col
TBL_TOP = Inches(1.28)
TH3    = Inches(0.38)          # header row height
TR3    = Inches(0.40)          # data row height

# Header
COL_NAMES = ["EBITDA Driver", "Today", "Yr 1", "Yr 2", "Yr 3", "Yr 4", "Yr 5"]
rect(s3, TM, TBL_TOP, TBL_W, TH3, fill=SLATE)
cx3 = TM
for j, nm in enumerate(COL_NAMES):
    algn = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
    off  = Inches(0.10) if j == 0 else Inches(0.04)
    cw   = DRV_W if j == 0 else DAT_W
    tb(s3, cx3 + off, TBL_TOP + Inches(0.09), cw - Inches(0.12), TH3 - Inches(0.09),
       nm, sz=8.5, bold=True, color=WHITE, align=algn)
    cx3 += cw

# Data rows
# (driver, tag_txt, tag_bg, row_bg, text_col, bold, [Today..Yr5])
EBITDA_ROWS = [
    ("Current base (95% retention/yr)", None, None,
     LIGHT_GRAY, DARK_TEXT, False,
     ["$150K", "$143K", "$136K", "$129K", "$122K", "$116K"]),
    ("SDR 1 \u2014 cumulative book", "raise", RED,
     WHITE, DARK_TEXT, False,
     ["\u2014", "$40K", "$98K", "$155K", "$210K", "$260K"]),
    ("SDR 2 \u2014 cumulative book", "raise", RED,
     LIGHT_GRAY, DARK_TEXT, False,
     ["\u2014", "\u2014", "$40K", "$98K", "$155K", "$210K"]),
    ("SDR 3 \u2014 cumulative book", "ops", SLATE,
     WHITE, DARK_TEXT, False,
     ["\u2014", "\u2014", "\u2014", "$40K", "$98K", "$155K"]),
    ("GovCon / set-aside (compounding)", None, None,
     LIGHT_GRAY, DARK_TEXT, False,
     ["\u2014", "$30K", "$64K", "$101K", "$141K", "$184K"]),
    ("Organic EBITDA", None, None,
     SLATE_DARK, WHITE, True,
     ["$150K", "$213K", "$338K", "$523K", "$726K", "$925K"]),
    ("Acquisition (opportunistic, mid yr 3)", "NewCo", GREEN,
     LIGHT_GREEN, GREEN, True,
     ["\u2014", "\u2014", "\u2014", "$200K", "$400K", "$400K"]),
    ("Organic + Inorganic EBITDA", None, None,
     RED, WHITE, True,
     ["$150K", "$213K", "$338K", "$723K", "$1.13M", "$1.32M"]),
]

for k, (drv, tag_txt, tag_bg, row_bg, tc_col, bold_row, vals) in enumerate(EBITDA_ROWS):
    ry3 = TBL_TOP + TH3 + k * TR3
    rect(s3, TM, ry3, TBL_W, TR3, fill=row_bg)
    # Driver text
    drv_tw = DRV_W - (Inches(0.64) if tag_txt else Inches(0.14))
    tb(s3, TM + Inches(0.10), ry3 + Inches(0.10),
       drv_tw, TR3 - Inches(0.10),
       drv, sz=8.5, bold=bold_row, color=tc_col)
    # Tag badge
    if tag_txt:
        badge(s3, TM + DRV_W - Inches(0.60),
              ry3 + (TR3 - Inches(0.17)) / 2,
              tag_txt, tag_bg, w=Inches(0.52))
    # Data values
    cx3v = TM + DRV_W
    for val in vals:
        tb(s3, cx3v + Inches(0.04), ry3 + Inches(0.10),
           DAT_W - Inches(0.08), TR3 - Inches(0.10),
           val, sz=9, bold=bold_row, color=tc_col, align=PP_ALIGN.CENTER)
        cx3v += DAT_W

# ── Two outcome banners ───────────────────────────────────────────────────────
TBL_BOT = TBL_TOP + TH3 + 8 * TR3
BNR_Y   = TBL_BOT + Inches(0.14)
BNR_H   = Inches(1.32)
HALF_W  = (TBL_W - Inches(0.14)) / 2   # ~6.377"

# Left banner — slate
LBX = TM
rect(s3, LBX, BNR_Y, HALF_W, BNR_H, fill=SLATE)
tb(s3, LBX + Inches(0.15), BNR_Y + Inches(0.08),
   HALF_W - Inches(0.25), Inches(0.22),
   "Organic only \u2014 Year 5", sz=9, color=MUTED_LIGHT)
tb(s3, LBX + Inches(0.15), BNR_Y + Inches(0.30),
   HALF_W - Inches(0.25), Inches(0.44),
   "$925K EBITDA", sz=22, bold=True, color=WHITE)
tb(s3, LBX + Inches(0.15), BNR_Y + Inches(0.76),
   HALF_W - Inches(0.25), Inches(0.48),
   "\u007e$4.6M valuation at 5x  \u00b7  above the $4M cap  \u00b7  clean investor exit",
   sz=9, color=MUTED_LIGHT, italic=True)

# Right banner — red
RBX = TM + HALF_W + Inches(0.14)
rect(s3, RBX, BNR_Y, HALF_W, BNR_H, fill=RED)
tb(s3, RBX + Inches(0.15), BNR_Y + Inches(0.08),
   HALF_W - Inches(0.25), Inches(0.22),
   "Organic + Acquisition \u2014 Year 4", sz=9, color=RED_MUTED)
tb(s3, RBX + Inches(0.15), BNR_Y + Inches(0.30),
   HALF_W - Inches(0.25), Inches(0.44),
   "$1.13M EBITDA", sz=22, bold=True, color=WHITE)
tb(s3, RBX + Inches(0.15), BNR_Y + Inches(0.76),
   HALF_W - Inches(0.25), Inches(0.48),
   "\u007e$5.6M valuation at 5x  \u00b7  well above cap  \u00b7  one year earlier",
   sz=9, color=RED_MUTED, italic=True)

# Footer (longer text — smaller font)
footer_bar(s3,
    "Acquisition structured at NewCo level \u2014 OpCo balance sheet stays clean for SBA recap  \u00b7  "
    "SDRs 1 & 2 raise funded, SDR 3 ops funded  \u00b7  "
    "GovCon: $30K yr 1 growing 15% annually with 95% retention  \u00b7  "
    "partnerships@maddogcleaning.com",
    sz=6.5)

# ── Save ──────────────────────────────────────────────────────────────────────
out = "/home/user/operations/MDF_Investor_Teaser_Final.pptx"
prs.save(out)
print(f"Saved: {out}")
