"""
MDF_Phase1.pptx — single slide
Red #B84C30 + Slate #3D4F5C | Arial | 960×540 px (10" × 5.625" at 96 dpi)
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from lxml import etree
from pptx.oxml.ns import qn

# ── Palette ───────────────────────────────────────────────────────────────────
RED         = RGBColor(0xB8, 0x4C, 0x30)
SLATE       = RGBColor(0x3D, 0x4F, 0x5C)
SLATE_MID   = RGBColor(0x6B, 0x80, 0x8F)
SLATE_DARK  = RGBColor(0x2C, 0x3A, 0x44)
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY  = RGBColor(0xF4, 0xF4, 0xF4)
LIGHT_SLATE = RGBColor(0xE6, 0xEB, 0xEE)
LIGHT_RED   = RGBColor(0xFB, 0xED, 0xE9)
GREEN       = RGBColor(0x2A, 0x7A, 0x3B)
LIGHT_GREEN = RGBColor(0xE8, 0xF5, 0xEB)
MID_GRAY    = RGBColor(0x8A, 0x93, 0x9C)
DARK_TEXT   = RGBColor(0x1E, 0x1E, 0x1E)
BORDER_GRAY = RGBColor(0xD4, 0xD8, 0xDC)
MUTED_LIGHT = RGBColor(0xA8, 0xBA, 0xC5)
RED_MUTED   = RGBColor(0xD4, 0x88, 0x74)
RED_DIV     = RGBColor(0xE2, 0xB4, 0xA7)
YELLOW      = RGBColor(0xF5, 0xC2, 0x0A)

# ── Dimensions (960×540 at 96 dpi = 10" × 5.625") ────────────────────────────
SLIDE_W  = Inches(10)
SLIDE_H  = Inches(5.625)
F        = "Arial"

HDR_H    = Inches(52  / 96)   # 0.5417"
PROOF_H  = Inches(46  / 96)   # 0.4792"
BTM_H    = Inches(54  / 96)   # 0.5625"
FOOTER_H = Inches(0.26)

PROOF_TOP  = HDR_H
COL_TOP    = HDR_H + PROOF_H
FOOTER_TOP = SLIDE_H - FOOTER_H
BTM_TOP    = FOOTER_TOP - BTM_H
COL_H      = BTM_TOP - COL_TOP   # ~3.297"
COL_W      = SLIDE_W / 3          # 3.333"

CPAD = Inches(0.18)               # inner horizontal padding per column
CW   = COL_W - 2 * CPAD          # usable content width per column ~2.973"

# ── Helpers ───────────────────────────────────────────────────────────────────
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
    if aL is None: aL = etree.SubElement(pG, qn('a:avLst'))
    for g in aL.findall(qn('a:gd')): aL.remove(g)
    gd = etree.SubElement(aL, qn('a:gd'))
    gd.set('name', 'adj'); gd.set('fmla', f'val {adj}')
    return shp

def tb(slide, l, t, w, h, text, sz=10, bold=False, color=DARK_TEXT,
       align=PP_ALIGN.LEFT, italic=False, wrap=True):
    txb = slide.shapes.add_textbox(l, t, w, h)
    txb.word_wrap = wrap
    tf = txb.text_frame
    tf.word_wrap = wrap; tf.auto_size = None
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
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE; tf.clear()
    for i, (txt, sz, bld, itl, col) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        run = p.add_run()
        run.text = txt; run.font.name = F
        run.font.size = Pt(sz); run.font.bold = bld
        run.font.italic = itl; run.font.color.rgb = col

def pill(slide, l, t, w, h, text, fill, tc=WHITE, sz=9):
    shp = rrect(slide, l, t, w, h, fill=fill, adj=50000)
    set_text(shp, [(text, sz, True, False, tc)])
    return shp

def col_label(slide, x, y, text, underline_color=RED):
    tb(slide, x + CPAD, y, CW, Inches(0.24),
       text, sz=10, bold=True, color=SLATE)
    rect(slide, x + CPAD, y + Inches(0.26), Inches(0.90), Pt(2), fill=underline_color)

def bullet_row(slide, x, y, w, text, sz=8.5, dot=SLATE):
    DOT = Inches(0.07)
    rect(slide, x + CPAD + Inches(0.02), y + Inches(0.06),
         DOT, DOT, fill=dot)
    tb(slide, x + CPAD + Inches(0.14), y,
       w - Inches(0.16), Inches(0.72),
       text, sz=sz, color=DARK_TEXT)

# ═══════════════════════════════════════════════════════════════════════════════
prs = Presentation()
prs.slide_width  = SLIDE_W
prs.slide_height = SLIDE_H
slide = prs.slide_layouts[6]   # blank
s = prs.slides.add_slide(slide)

# ── White background ──────────────────────────────────────────────────────────
rect(s, 0, 0, SLIDE_W, SLIDE_H, fill=WHITE)

# ════════════════════════════════════════════════════════════════════════════
# HEADER BAR
# ════════════════════════════════════════════════════════════════════════════
rect(s, 0, 0, SLIDE_W, HDR_H, fill=SLATE)

# Title
tb(s, Inches(0.18), Inches(0.06), Inches(6.2), Inches(0.28),
   "Phase 1 \u2014 building the organic growth engine",
   sz=14, bold=True, color=WHITE)

# Subtitle
tb(s, Inches(0.18), Inches(0.35), Inches(6.0), Inches(0.18),
   "$200K raise  \u00b7  Prove the thesis before accelerating through M&A",
   sz=8, color=SLATE_MID)

# Red pill badge on the right
BADGE_W = Inches(3.10)
BADGE_H = Inches(0.34)
BADGE_X = SLIDE_W - Inches(0.14) - BADGE_W
BADGE_Y = (HDR_H - BADGE_H) / 2
pill(s, BADGE_X, BADGE_Y, BADGE_W, BADGE_H,
     "Convertible Note  \u00b7  10% PIK  \u00b7  15% equity  \u00b7  4-yr maturity",
     fill=RED, sz=8.5)

# ════════════════════════════════════════════════════════════════════════════
# PROOF BAR
# ════════════════════════════════════════════════════════════════════════════
# Light red background
rect(s, 0, PROOF_TOP, SLIDE_W, PROOF_H, fill=LIGHT_RED)
# Red left border
rect(s, 0, PROOF_TOP, Inches(0.042), PROOF_H, fill=RED)

# Stats layout
STAT_LEFT  = Inches(0.10)
STAT_W     = Inches(1.38)
DIV_W      = Inches(0.012)

STATS = [
    ("$170K",      "ARR added"),
    ("4 months",   "Time to add"),
    ("Fractional", "Sales effort"),
    ("0",          "Dedicated SDRs"),
]

VY = PROOF_TOP + Inches(0.06)    # value y
LY = PROOF_TOP + Inches(0.27)    # label y
VH = Inches(0.21)
LH = Inches(0.16)

for i, (val, lbl) in enumerate(STATS):
    sx = STAT_LEFT + i * (STAT_W + DIV_W)
    # Vertical divider before each stat except first
    if i > 0:
        rect(s, sx - DIV_W - Inches(0.002), PROOF_TOP + Inches(0.07),
             Inches(0.008), PROOF_H - Inches(0.14), fill=RED_DIV)
    # Value (bold red)
    tb(s, sx + Inches(0.06), VY, STAT_W - Inches(0.08), VH,
       val, sz=12, bold=True, color=RED, align=PP_ALIGN.LEFT)
    # Label (small slate-mid)
    tb(s, sx + Inches(0.06), LY, STAT_W - Inches(0.08), LH,
       lbl, sz=7, color=SLATE_MID, align=PP_ALIGN.LEFT)

# Vertical divider between stats and italic text
STATS_END_X = STAT_LEFT + 4 * STAT_W + 3 * DIV_W
rect(s, STATS_END_X + Inches(0.10), PROOF_TOP + Inches(0.07),
     Inches(0.008), PROOF_H - Inches(0.14), fill=RED_DIV)

# Italic red proof text
PROOF_TX = STATS_END_X + Inches(0.18)
PROOF_TW = SLIDE_W - PROOF_TX - Inches(0.14)
tb(s, PROOF_TX, PROOF_TOP + Inches(0.05),
   PROOF_TW, PROOF_H - Inches(0.08),
   "We proved we can add material MRR with a lean, fractional team. "
   "This raise funds doing it full-time with dedicated resources for the first time.",
   sz=7.5, italic=True, color=RED)

# ════════════════════════════════════════════════════════════════════════════
# COLUMN BACKGROUNDS + DIVIDERS
# ════════════════════════════════════════════════════════════════════════════
C1X = Inches(0)
C2X = COL_W
C3X = COL_W * 2

# Subtle alternating backgrounds
rect(s, C1X, COL_TOP, COL_W, COL_H, fill=WHITE)
rect(s, C2X, COL_TOP, COL_W, COL_H, fill=LIGHT_GRAY)
rect(s, C3X, COL_TOP, COL_W, COL_H, fill=WHITE)

# Thin vertical dividers
rect(s, C2X, COL_TOP, Inches(0.007), COL_H, fill=BORDER_GRAY)
rect(s, C3X, COL_TOP, Inches(0.007), COL_H, fill=BORDER_GRAY)


# ════════════════════════════════════════════════════════════════════════════
# COLUMN 1 — "Why organic first"
# ════════════════════════════════════════════════════════════════════════════
CTY = COL_TOP + Inches(0.16)        # column title y
BY  = CTY + Inches(0.34)            # bullets start y
BH  = Inches(0.80)                  # height per bullet (allows wrapping)

col_label(s, C1X, CTY, "Why organic first", underline_color=RED)

C1_BULLETS = [
    "Cleaning businesses have inherent churn risk \u2014 acquiring revenue before you can "
    "retain and grow it organically is a trap",
    "The smart play is to prove organic growth first, build infrastructure to retain "
    "what you win, then use M&A to accelerate a proven model",
    "M&A on top of a weak organic engine papers over the problem \u2014 "
    "M&A on top of a strong one compounds it",
]
for j, b in enumerate(C1_BULLETS):
    bullet_row(s, C1X, BY + j * BH, COL_W, b, dot=SLATE)

PILL_Y1 = BY + len(C1_BULLETS) * BH + Inches(0.16)
pill(s, C1X + CPAD, PILL_Y1, CW, Inches(0.36),
     "Phase 1 de-risks Phase 2 entirely", fill=SLATE, sz=8.5)

# ════════════════════════════════════════════════════════════════════════════
# COLUMN 2 — "What this raise funds"
# ════════════════════════════════════════════════════════════════════════════
BH2 = Inches(0.64)

col_label(s, C2X, CTY, "What this raise funds", underline_color=RED)

C2_BULLETS = [
    "2 full-time SDRs over 12 months \u2014 the proven channel now at full capacity, "
    "targeting $50\u201375K MRR growth per quarter per SDR",
    "Working capital to service growth without cash flow strain",
    "Admin infrastructure \u2014 PM, bookkeeper, office manager \u2014 to handle "
    "increased volume professionally",
    "GovCon analyst to capture SDVOSB set-aside RFP pipeline \u2014 "
    "targeting $150K+ ARR in sticky, recurring government contracts",
]
for j, b in enumerate(C2_BULLETS):
    bullet_row(s, C2X, BY + j * BH2, COL_W, b, dot=RED)

PILL_Y2 = BY + len(C2_BULLETS) * BH2 + Inches(0.14)
pill(s, C2X + CPAD, PILL_Y2, CW, Inches(0.36),
     "$200K funds the engine \u2014 not the acquisition", fill=RED, sz=8.5)

# ════════════════════════════════════════════════════════════════════════════
# COLUMN 3 — "Phase 2 — what success unlocks"
# ════════════════════════════════════════════════════════════════════════════
col_label(s, C3X, CTY, "Phase 2 \u2014 what success unlocks", underline_color=GREEN)

C3_BULLETS = [
    "Organic engine proven \u2014 consistent MRR growth, retention validated, "
    "GovCon pipeline converting",
    "Geographic expansion into new markets with existing SDVOSB footprint",
    "Bolt-on acquisitions of retiring owner-operators \u2014 lower risk on a proven platform",
    "Phase 1 investors receive right of first refusal on Phase 2 capital opportunities",
]
for j, b in enumerate(C3_BULLETS):
    bullet_row(s, C3X, BY + j * BH2, COL_W, b, dot=GREEN)

PILL_Y3 = BY + len(C3_BULLETS) * BH2 + Inches(0.14)
pill(s, C3X + CPAD, PILL_Y3, CW, Inches(0.36),
     "Phase 2 is acceleration \u2014 not a pivot", fill=GREEN, sz=8.5)


# ════════════════════════════════════════════════════════════════════════════
# BOTTOM 2-COLUMN BAND
# ════════════════════════════════════════════════════════════════════════════
HALF_W = SLIDE_W / 2    # 5"
BPAD   = Inches(0.16)   # inner horizontal padding
BFZ    = 6.5            # bottom band small font size

# ── Left — slate ──────────────────────────────────────────────────────────
rect(s, 0, BTM_TOP, HALF_W, BTM_H, fill=SLATE)

def btm_text(slide, l, t, w, h, label, title, body,
             label_col, title_col, body_col, title_sz=10):
    txb = slide.shapes.add_textbox(l, t, w, h)
    txb.word_wrap = True
    tf = txb.text_frame
    tf.word_wrap = True; tf.auto_size = None
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.clear()

    # Para 1: label
    p0 = tf.paragraphs[0]; p0.alignment = PP_ALIGN.LEFT
    r0 = p0.add_run()
    r0.text = label; r0.font.name = F
    r0.font.size = Pt(6.5); r0.font.bold = False
    r0.font.color.rgb = label_col

    # Para 2: bold title
    p1 = tf.add_paragraph(); p1.alignment = PP_ALIGN.LEFT
    r1 = p1.add_run()
    r1.text = title; r1.font.name = F
    r1.font.size = Pt(title_sz); r1.font.bold = True
    r1.font.color.rgb = title_col
    p1.space_before = Pt(1)

    # Para 3: small body
    p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.LEFT
    r2 = p2.add_run()
    r2.text = body; r2.font.name = F
    r2.font.size = Pt(BFZ); r2.font.bold = False
    r2.font.color.rgb = body_col
    p2.space_before = Pt(1)

btm_text(
    s,
    BPAD, BTM_TOP + Inches(0.04),
    HALF_W - 2 * BPAD, BTM_H - Inches(0.06),
    label="Phase 1 \u2014 now",
    title="$200K  \u00b7  Organic engine",
    body="2 SDRs  \u00b7  GovCon team ($150K+ ARR target)  \u00b7  "
         "Admin infrastructure  \u00b7  Working capital  \u00b7  "
         "Prove $50\u201375K MRR/qtr per SDR",
    label_col=MUTED_LIGHT, title_col=WHITE, body_col=MUTED_LIGHT,
    title_sz=10,
)

# ── Right — light red with red left border ────────────────────────────────
rect(s, HALF_W, BTM_TOP, HALF_W, BTM_H, fill=LIGHT_RED)
rect(s, HALF_W, BTM_TOP, Inches(0.042), BTM_H, fill=RED)

btm_text(
    s,
    HALF_W + Inches(0.042) + BPAD, BTM_TOP + Inches(0.04),
    HALF_W - Inches(0.042) - 2 * BPAD, BTM_H - Inches(0.06),
    label="Phase 2 \u2014 unlocked by Phase 1 success",
    title="M&A + Geographic expansion",
    body="Bolt-on acquisitions  \u00b7  New markets  \u00b7  Platform scale  \u00b7  "
         "Phase 1 investors get ROFR on Phase 2 opportunities",
    label_col=RED_MUTED, title_col=RED, body_col=MID_GRAY,
    title_sz=10,
)

# ════════════════════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════════════════════
tb(s, Inches(0.2), FOOTER_TOP + Inches(0.04),
   SLIDE_W - Inches(0.4), FOOTER_H - Inches(0.04),
   "partnerships@maddogcleaning.com  \u00b7  "
   "Confidential \u2014 not an offer to sell securities  \u00b7  March 2026",
   sz=6.5, color=MID_GRAY, align=PP_ALIGN.CENTER)

# ════════════════════════════════════════════════════════════════════════════
out = "/home/user/operations/MDF_Phase1.pptx"
prs.save(out)
print(f"Saved: {out}")
