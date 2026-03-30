"""
Build MDF_Investor_Teaser.pptx
"""
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
from pptx.oxml.ns import qn
from pptx.oxml import parse_xml
from lxml import etree
import copy

# ── Palette ────────────────────────────────────────────────────────────────────
NAVY        = RGBColor(0x0D, 0x1F, 0x3C)   # dark navy
NAVY_MID    = RGBColor(0x1A, 0x35, 0x5C)   # slightly lighter navy
GOLD        = RGBColor(0xC9, 0xA0, 0x2C)   # accent gold
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY  = RGBColor(0xF4, 0xF6, 0xF9)
MID_GRAY    = RGBColor(0xD0, 0xD5, 0xDE)
DARK_TEXT   = RGBColor(0x1A, 0x1A, 0x2E)
GREEN       = RGBColor(0x2E, 0x7D, 0x32)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# ── Helpers ────────────────────────────────────────────────────────────────────
def add_rect(slide, l, t, w, h, fill_rgb=None, line_rgb=None, line_pt=0):
    shape = slide.shapes.add_shape(1, l, t, w, h)  # MSO_SHAPE_TYPE.RECTANGLE = 1
    shape.line.width = Pt(line_pt) if line_pt else Pt(0)
    if fill_rgb:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_rgb
    else:
        shape.fill.background()
    if line_rgb:
        shape.line.color.rgb = line_rgb
        shape.line.width = Pt(line_pt if line_pt else 0.75)
    else:
        shape.line.fill.background()
    return shape

def add_textbox(slide, l, t, w, h, text, font_size=11, bold=False, color=DARK_TEXT,
                align=PP_ALIGN.LEFT, italic=False, wrap=True):
    txb = slide.shapes.add_textbox(l, t, w, h)
    txb.word_wrap = wrap
    tf = txb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = "Calibri"
    return txb

def add_text_in_shape(slide, shape, lines, font_size=11, bold=False, color=WHITE,
                       align=PP_ALIGN.CENTER, v_anchor="middle"):
    """Add multi-line text to an existing shape."""
    tf = shape.text_frame
    tf.word_wrap = True
    if v_anchor == "middle":
        tf.auto_size = None
        from pptx.enum.text import MSO_ANCHOR
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.clear()
    for i, (txt, sz, bld, itl) in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.alignment = align
        run = p.add_run()
        run.text = txt
        run.font.size = Pt(sz)
        run.font.bold = bld
        run.font.italic = itl
        run.font.color.rgb = color
        run.font.name = "Calibri"

def set_shape_text(shape, text, font_size, bold, color, align, italic=False):
    tf = shape.text_frame
    tf.word_wrap = True
    from pptx.enum.text import MSO_ANCHOR
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.clear()
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = "Calibri"

# ── Chart helper ───────────────────────────────────────────────────────────────
def make_bar_chart():
    fig, ax = plt.subplots(figsize=(7.5, 2.2), facecolor="#F4F6F9")
    ax.set_facecolor("#F4F6F9")

    labels = ["Year 3 Exit (~$620K payout, ~2.1x MOIC)", "Year 5 Exit (~$1.05M payout, ~3.5x MOIC)"]
    values = [620, 1050]
    colors = ["#1A355C", "#C9A02C"]

    bars = ax.barh(labels, values, color=colors, height=0.45, edgecolor="none")
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 15, bar.get_y() + bar.get_height() / 2,
                f"${val:,}K", va="center", ha="left", fontsize=11,
                fontweight="bold", color="#1A1A2E", fontfamily="DejaVu Sans")

    ax.set_xlim(0, 1300)
    ax.set_xlabel("Illustrative Investor Payout ($K)", fontsize=9, color="#555")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", labelsize=9.5, colors="#1A1A2E")
    ax.tick_params(axis="x", labelsize=8, colors="#777")
    ax.set_title("Illustrative Investor Returns on $300K Note", fontsize=11,
                 fontweight="bold", color="#0D1F3C", pad=8)
    fig.tight_layout(pad=0.4)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight", facecolor="#F4F6F9")
    plt.close(fig)
    buf.seek(0)
    return buf


# ══════════════════════════════════════════════════════════════════════════════
#  BUILD PRESENTATION
# ══════════════════════════════════════════════════════════════════════════════
prs = Presentation()
prs.slide_width  = SLIDE_W
prs.slide_height = SLIDE_H

blank_layout = prs.slide_layouts[6]  # completely blank

# ═══════════════════════════════════════════════════════════════════════════════
#  SLIDE 1
# ═══════════════════════════════════════════════════════════════════════════════
s1 = prs.slides.add_slide(blank_layout)

# ── Background ─────────────────────────────────────────────────────────────────
bg = add_rect(s1, 0, 0, SLIDE_W, SLIDE_H, fill_rgb=LIGHT_GRAY)

# ── Header bar ─────────────────────────────────────────────────────────────────
HEADER_H = Inches(1.05)
hdr = add_rect(s1, 0, 0, SLIDE_W, HEADER_H, fill_rgb=NAVY)

# Gold accent strip under header
add_rect(s1, 0, HEADER_H, SLIDE_W, Pt(4), fill_rgb=GOLD)

# Header title
add_text_in_shape(s1, hdr,
    [("Mad Dog Facility Partners — Confidential Investor Teaser", 22, True, False),
     ("SDVOSB  ·  Janitorial & Facility Services  ·  IL  ·  WI  ·  AZ  ·  TX", 12, False, False)],
    color=WHITE, align=PP_ALIGN.CENTER)

# ── Metric boxes ───────────────────────────────────────────────────────────────
METRICS = [
    ("2025 Revenue", "$693K", "+19% vs 2024"),
    ("2025 Net Income", "$134K", "19% margin"),
    ("Current MRR", "~$50K", "+$170K ARR added YTD"),
    ("Raise", "$300K", "Convertible Note"),
]
BOX_TOP  = Inches(1.18)
BOX_H    = Inches(1.12)
BOX_GAP  = Inches(0.18)
MARGIN   = Inches(0.30)
BOX_W    = (SLIDE_W - 2*MARGIN - 3*BOX_GAP) / 4

for i, (label, value, sub) in enumerate(METRICS):
    x = MARGIN + i * (BOX_W + BOX_GAP)
    box = add_rect(s1, x, BOX_TOP, BOX_W, BOX_H, fill_rgb=NAVY_MID, line_rgb=GOLD, line_pt=1.5)
    add_text_in_shape(s1, box,
        [(label, 9,  False, False),
         (value,  20, True,  False),
         (sub,    8,  False, False)],
        color=WHITE, align=PP_ALIGN.CENTER)

# ── Two-column section ─────────────────────────────────────────────────────────
COL_TOP   = Inches(2.42)
COL_H     = Inches(3.88)
COL_W     = (SLIDE_W - 2*MARGIN - Inches(0.20)) / 2
COL_R_X   = MARGIN + COL_W + Inches(0.20)

# Left column card
left_card = add_rect(s1, MARGIN, COL_TOP, COL_W, COL_H, fill_rgb=WHITE,
                     line_rgb=MID_GRAY, line_pt=0.75)

# Left header strip
lh = add_rect(s1, MARGIN, COL_TOP, COL_W, Inches(0.33), fill_rgb=NAVY)
add_textbox(s1, MARGIN + Inches(0.12), COL_TOP + Pt(4), COL_W - Inches(0.12), Inches(0.33),
            "The story so far", 11, True, WHITE, PP_ALIGN.LEFT)

BULLET_LINES = [
    ("Acquired at $425K revenue in 2024, grew to $693K by end of 2025.", False),
    ("Lost largest customer Sept 2025 — $336K ARR gone overnight.", False),
    ("Added $170K ARR in under 4 months on fractional sales effort with no dedicated SDR.", False),
    ("2026 Q1 at ~$141K revenue (including $33K in AR) — run rate on recovery trajectory.", False),
]
BULLET_TOP = COL_TOP + Inches(0.40)
for j, (txt, _) in enumerate(BULLET_LINES):
    by = BULLET_TOP + j * Inches(0.57)
    # bullet dot
    dot = add_rect(s1, MARGIN + Inches(0.14), by + Inches(0.09), Inches(0.07), Inches(0.07),
                   fill_rgb=GOLD)
    add_textbox(s1, MARGIN + Inches(0.28), by, COL_W - Inches(0.38), Inches(0.55),
                txt, 9.5, False, DARK_TEXT, PP_ALIGN.LEFT)

# Italic footnote
fn_y = BULLET_TOP + len(BULLET_LINES) * Inches(0.57) + Inches(0.05)
add_textbox(s1, MARGIN + Inches(0.14), fn_y, COL_W - Inches(0.28), Inches(0.45),
            "We did this part-time. Imagine what a full-time SDR unlocks.",
            9, False, NAVY_MID, PP_ALIGN.LEFT, italic=True)

# Right column card
right_card = add_rect(s1, COL_R_X, COL_TOP, COL_W, COL_H, fill_rgb=WHITE,
                      line_rgb=MID_GRAY, line_pt=0.75)

rh = add_rect(s1, COL_R_X, COL_TOP, COL_W, Inches(0.33), fill_rgb=NAVY)
add_textbox(s1, COL_R_X + Inches(0.12), COL_TOP + Pt(4), COL_W - Inches(0.12), Inches(0.33),
            "Use of proceeds", 11, True, WHITE, PP_ALIGN.LEFT)

# Use-of-proceeds table
UOP = [
    ("SDR hire (base + ramp)",   "$110K"),
    ("Founder comp increase",     "$20K"),
    ("Working capital cushion",   "$40K"),
    ("M&A dry powder",            "$130K"),
    ("Total",                     "$300K"),
]
TABLE_TOP = COL_TOP + Inches(0.38)
ROW_H = Inches(0.39)
for k, (item, amt) in enumerate(UOP):
    ry = TABLE_TOP + k * ROW_H
    row_fill = LIGHT_GRAY if k % 2 == 0 else WHITE
    is_total = (k == len(UOP) - 1)
    if is_total:
        row_fill = NAVY
    row_bg = add_rect(s1, COL_R_X + Inches(0.10), ry,
                      COL_W - Inches(0.20), ROW_H, fill_rgb=row_fill)
    txt_col = WHITE if is_total else DARK_TEXT
    add_textbox(s1, COL_R_X + Inches(0.18), ry + Pt(3),
                COL_W - Inches(0.60), ROW_H - Pt(6),
                item, 9.5, is_total, txt_col, PP_ALIGN.LEFT)
    add_textbox(s1, COL_R_X + COL_W - Inches(0.72), ry + Pt(3),
                Inches(0.55), ROW_H - Pt(6),
                amt, 9.5, is_total, txt_col, PP_ALIGN.RIGHT)

# Note terms boxes (4 small boxes)
NOTE_TERMS = [
    ("Amount", "$300K"),
    ("PIK Rate", "15%/yr"),
    ("Maturity", "3yr + 2yr option"),
    ("Val. Cap", "$3.5M"),
]
NT_TOP = TABLE_TOP + len(UOP) * ROW_H + Inches(0.12)
NT_W = (COL_W - Inches(0.20) - 3*Inches(0.06)) / 4
for m, (lbl, val) in enumerate(NOTE_TERMS):
    nx = COL_R_X + Inches(0.10) + m * (NT_W + Inches(0.06))
    nb = add_rect(s1, nx, NT_TOP, NT_W, Inches(0.62),
                  fill_rgb=NAVY_MID, line_rgb=GOLD, line_pt=1.2)
    add_text_in_shape(s1, nb,
        [(lbl, 7.5, False, False),
         (val,  9.5, True,  False)],
        color=WHITE, align=PP_ALIGN.CENTER)

# ── Footer ─────────────────────────────────────────────────────────────────────
FOOTER_Y = SLIDE_H - Inches(0.32)
add_rect(s1, 0, FOOTER_Y, SLIDE_W, Inches(0.32), fill_rgb=NAVY)
add_textbox(s1, Inches(0.2), FOOTER_Y + Pt(3), SLIDE_W - Inches(0.4), Inches(0.28),
            "partnerships@maddogcleaning.com  ·  Confidential — not an offer to sell securities  ·  March 2026",
            7.5, False, WHITE, PP_ALIGN.CENTER)


# ═══════════════════════════════════════════════════════════════════════════════
#  SLIDE 2
# ═══════════════════════════════════════════════════════════════════════════════
s2 = prs.slides.add_slide(blank_layout)

# Background
add_rect(s2, 0, 0, SLIDE_W, SLIDE_H, fill_rgb=LIGHT_GRAY)

# Header bar
hdr2 = add_rect(s2, 0, 0, SLIDE_W, HEADER_H, fill_rgb=NAVY)
add_rect(s2, 0, HEADER_H, SLIDE_W, Pt(4), fill_rgb=GOLD)
add_text_in_shape(s2, hdr2,
    [("Why this works — growth thesis and returns", 22, True, False)],
    color=WHITE, align=PP_ALIGN.CENTER)

# ── 3-column thesis cards ──────────────────────────────────────────────────────
THESIS = [
    ("Proven Channel",
     "Proven playbook",
     "$170K ARR added in under 4 months on fractional effort. A dedicated SDR is the multiplier on an already-proven playbook."),
    ("M&A Pipeline",
     "Acquisition-led growth",
     "LOI out on a Midwest target at $1.1M revenue, expected to contribute ~$150K EBITDA. Acquisition-led growth is the long game."),
    ("SDVOSB Moat",
     "Structural advantage",
     "Set-aside certifications, multi-state footprint, and 8-figure industry mentors. Not a standing-start bet."),
]

TC_TOP = Inches(1.18)
TC_H   = Inches(1.80)
TC_GAP = Inches(0.18)
TC_W   = (SLIDE_W - 2*MARGIN - 2*TC_GAP) / 3

for i, (title, subtitle, body) in enumerate(THESIS):
    tx = MARGIN + i * (TC_W + TC_GAP)
    card = add_rect(s2, tx, TC_TOP, TC_W, TC_H, fill_rgb=WHITE,
                    line_rgb=MID_GRAY, line_pt=0.75)
    # coloured top strip
    strip = add_rect(s2, tx, TC_TOP, TC_W, Inches(0.30), fill_rgb=NAVY)
    add_textbox(s2, tx + Inches(0.12), TC_TOP + Pt(4), TC_W - Inches(0.16), Inches(0.30),
                title, 10.5, True, WHITE, PP_ALIGN.LEFT)
    # subtitle in gold
    add_textbox(s2, tx + Inches(0.12), TC_TOP + Inches(0.32), TC_W - Inches(0.16), Inches(0.28),
                subtitle, 8.5, False, GOLD, PP_ALIGN.LEFT, italic=True)
    # body
    add_textbox(s2, tx + Inches(0.12), TC_TOP + Inches(0.60), TC_W - Inches(0.18), TC_H - Inches(0.68),
                body, 9.5, False, DARK_TEXT, PP_ALIGN.LEFT)

# ── Bar chart ─────────────────────────────────────────────────────────────────
chart_img = make_bar_chart()
CHART_TOP = TC_TOP + TC_H + Inches(0.18)
CHART_H   = Inches(2.15)
CHART_W   = SLIDE_W - 2*MARGIN
s2.shapes.add_picture(chart_img, MARGIN, CHART_TOP, CHART_W, CHART_H)

# ── Footnote ──────────────────────────────────────────────────────────────────
FN_Y = CHART_TOP + CHART_H + Inches(0.04)
add_textbox(s2, MARGIN, FN_Y, SLIDE_W - 2*MARGIN, Inches(0.28),
    "Yr 5 assumes $1M EBITDA at 5x valuation ($5M). Investor owns 8.6% equity ($300K/$3.5M cap) plus full PIK accrual. Yr 3 exit assumes $3M valuation.",
    7.5, False, RGBColor(0x55,0x55,0x55), PP_ALIGN.CENTER, italic=True)

# ── Bottom banner ─────────────────────────────────────────────────────────────
BANNER_Y = FN_Y + Inches(0.30)
BANNER_H = Inches(0.44)
banner = add_rect(s2, MARGIN, BANNER_Y, SLIDE_W - 2*MARGIN, BANNER_H,
                  fill_rgb=NAVY_MID, line_rgb=GOLD, line_pt=1.2)
add_text_in_shape(s2, banner,
    [("Target: $5–6M revenue · $1M EBITDA within 5 years via organic growth + M&A. "
      "Recap via SBA at maturity returns capital to investors cleanly.", 9.5, False, False)],
    color=WHITE, align=PP_ALIGN.CENTER)

# ── Footer ─────────────────────────────────────────────────────────────────────
add_rect(s2, 0, FOOTER_Y, SLIDE_W, Inches(0.32), fill_rgb=NAVY)
add_textbox(s2, Inches(0.2), FOOTER_Y + Pt(3), SLIDE_W - Inches(0.4), Inches(0.28),
            "partnerships@maddogcleaning.com  ·  Confidential — not an offer to sell securities  ·  March 2026",
            7.5, False, WHITE, PP_ALIGN.CENTER)

# ── Save ───────────────────────────────────────────────────────────────────────
out = "/home/user/operations/MDF_Investor_Teaser.pptx"
prs.save(out)
print(f"Saved: {out}")
