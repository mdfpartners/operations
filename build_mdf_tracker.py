"""
MDF Operations Tracker — McKinsey/Deloitte-style Excel builder + OneDrive upload
"""

import os
import sys
import requests
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule

# ── Palette ───────────────────────────────────────────────────────────────────
NAVY          = "00338D"   # McKinsey deep blue
NAVY_MID      = "003A70"   # KPI tile header
NAVY_LIGHT    = "D6E4F0"   # light accent
WHITE         = "FFFFFF"
SLATE_LIGHT   = "F4F6FA"   # alt row
SLATE_LINE    = "CBD4E1"   # border

# Status fills — bold, saturated
RED_FILL      = "FFCDD2"
RED_TEXT      = "B71C1C"
AMBER_FILL    = "FFF3CD"
AMBER_TEXT    = "7B4F00"
GREEN_FILL    = "C8E6C9"
GREEN_TEXT    = "1B5E20"
GREY_FILL     = "E0E0E0"
GREY_TEXT     = "424242"

# Priority chips
PRI_HIGH      = "FFCDD2"
PRI_MED       = "FFF3CD"
PRI_LOW       = "DCEEFB"

# Accountability header
DEEP_RED      = "B71C1C"

FONT_NAME     = "Calibri"

DATE_FMT      = "M/D/YY"

# ── Helpers ───────────────────────────────────────────────────────────────────

def f(hex_color):
    return PatternFill("solid", fgColor=hex_color)

def border(color=SLATE_LINE):
    s = Side(style="thin", color=color)
    return Border(left=s, right=s, top=s, bottom=s)

def font(size=10, bold=False, color="000000", name=FONT_NAME):
    return Font(name=name, size=size, bold=bold, color=color)

def align(h="left", v="center", wrap=False):
    return Alignment(horizontal=h, vertical=v, wrap_text=wrap)

def hdr_cell(ws, row, col, value, bg=NAVY, fg=WHITE, size=10, h="center"):
    c = ws.cell(row=row, column=col, value=value)
    c.font = font(size=size, bold=True, color=fg)
    c.fill = f(bg)
    c.alignment = align(h=h)
    c.border = border()
    return c

def body_cell(ws, row, col, value, bg=None, fg="000000", bold=False, h="left", wrap=False, num_fmt=None):
    c = ws.cell(row=row, column=col, value=value)
    c.font = font(size=10, bold=bold, color=fg)
    c.alignment = align(h=h, wrap=wrap)
    c.border = border()
    if bg:
        c.fill = f(bg)
    if num_fmt:
        c.number_format = num_fmt
    return c

def set_col_widths(ws, widths):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

def section_title(ws, row, col, text, span=6, bg=NAVY_LIGHT):
    c = ws.cell(row=row, column=col, value=text)
    c.font = font(size=11, bold=True, color=NAVY)
    c.fill = f(bg)
    c.alignment = align(h="left", v="center")
    c.border = border(NAVY)
    ws.row_dimensions[row].height = 20
    end_col = get_column_letter(col + span - 1)
    ws.merge_cells(f"{get_column_letter(col)}{row}:{end_col}{row}")

def write_header_row(ws, row, headers, bg=NAVY, fg=WHITE, height=20):
    for ci, h in enumerate(headers, 1):
        hdr_cell(ws, row, ci, h, bg=bg, fg=fg)
    ws.row_dimensions[row].height = height

def status_dot(status):
    mapping = {
        "Green":    "● Green",
        "Yellow":   "● Yellow",
        "Red":      "● Red",
        "On Track": "● On Track",
        "At Risk":  "● At Risk",
        "Behind":   "● Behind",
        "Complete": "✓ Done",
    }
    return mapping.get(status, status)

def flag_fill(flag):
    if flag in ("Red", "● Red"):       return RED_FILL
    if flag in ("Yellow", "● Yellow"): return AMBER_FILL
    if flag in ("Green", "● Green"):   return GREEN_FILL
    return None

def flag_text_color(flag):
    if flag in ("Red", "● Red"):       return RED_TEXT
    if flag in ("Yellow", "● Yellow"): return AMBER_TEXT
    if flag in ("Green", "● Green"):   return GREEN_TEXT
    return "000000"

def add_dropdown(ws, formula, sqref):
    dv = DataValidation(type="list", formula1=formula, allow_blank=True, showErrorMessage=False)
    dv.sqref = sqref
    ws.add_data_validation(dv)

def apply_flag_cf(ws, col_letter, start_row, end_row):
    rng = f"{col_letter}{start_row}:{col_letter}{end_row}"
    for val, fill in [("Green", GREEN_FILL), ("Yellow", AMBER_FILL), ("Red", RED_FILL)]:
        ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=[f'"{val}"'], fill=f(fill)))

# ── Tab 1 — Dashboard ─────────────────────────────────────────────────────────

def build_dashboard(wb):
    ws = wb.create_sheet("Dashboard")
    ws.sheet_view.showGridLines = False
    ws.sheet_view.showRowColHeaders = False

    set_col_widths(ws, [3, 22, 22, 22, 22, 22, 3])

    # ── Title bar ──
    ws.row_dimensions[1].height = 8   # top margin
    c = ws.cell(row=2, column=2, value="MDF OPERATIONS TRACKER")
    c.font = font(size=16, bold=True, color=WHITE)
    c.fill = f(NAVY)
    c.alignment = align(h="left", v="center")
    ws.merge_cells("B2:F2")
    ws.row_dimensions[2].height = 34

    c2 = ws.cell(row=3, column=2, value="Week of 3/24/26  |  Facility Operations  |  Live Status")
    c2.font = font(size=10, bold=False, color=WHITE)
    c2.fill = f(NAVY_MID)
    c2.alignment = align(h="left", v="center")
    ws.merge_cells("B3:F3")
    ws.row_dimensions[3].height = 18

    ws.row_dimensions[4].height = 10  # spacer

    # ── KPI Tiles ──
    kpis = [
        ("5",    "Open Flags"),
        ("3",    "At-Risk Projects"),
        ("88%",  "Wk Completion Rate"),
        ("14",   "Open Work Orders"),
        ("3",    "Overdue Actions"),
    ]

    tile_bg   = [NAVY_MID, "C62828", "E65100", "C62828", "B71C1C"]
    tile_cols = [2, 3, 4, 5, 6]

    for (val, label), bg, col in zip(kpis, tile_bg, tile_cols):
        big = ws.cell(row=5, column=col, value=val)
        big.font = Font(name=FONT_NAME, size=22, bold=True, color=WHITE)
        big.fill = f(bg)
        big.alignment = align(h="center", v="bottom")
        lbl = ws.cell(row=6, column=col, value=label)
        lbl.font = font(size=9, bold=False, color=WHITE)
        lbl.fill = f(bg)
        lbl.alignment = align(h="center", v="top")

    ws.row_dimensions[5].height = 30
    ws.row_dimensions[6].height = 18
    ws.row_dimensions[7].height = 12  # spacer

    # ── Open Flags ──
    section_title(ws, 8, 2, "  ⚑  URGENT FLAGS — Requires Action", span=5)

    flag_hdrs = ["Source", "Task / Initiative", "Owner", "Flag", "Callout"]
    for ci, h in enumerate(flag_hdrs, 2):
        hdr_cell(ws, 9, ci, h, bg=NAVY)
    ws.row_dimensions[9].height = 18

    flag_rows = [
        ["Weekly", "HVAC filter replacement — Unit 4B",       "R. Patel",   "Red",    "3 weeks overdue — parts backorder"],
        ["Adhoc",  "Q2 janitorial contract renewal",          "M. Torres",  "Red",    "Legal redlines outstanding since 3/12/26"],
        ["Weekly", "Overnight cleaning crew sign-in",         "M. Torres",  "Yellow", "Wed crew +22 min late"],
        ["Adhoc",  "Vendor credentialing portal rollout",     "K. Johnson", "Yellow", "IT delayed 2 sprints → new ETA 4/15/26"],
        ["Adhoc",  "Staff training — work-order app",         "J. Carter",  "Yellow", "Vendor training deck still pending"],
    ]

    for ri, row in enumerate(flag_rows, 10):
        flag     = row[3]
        fill_clr = flag_fill(flag)
        tc       = flag_text_color(flag)
        row_bg   = SLATE_LIGHT if ri % 2 == 0 else None
        for ci, val in zip(range(2, 7), row):
            body_cell(ws, ri, ci, val, bg=row_bg)
        c = ws.cell(row=ri, column=5, value=status_dot(flag))
        c.font = font(size=10, bold=True, color=tc)
        c.fill = f(fill_clr) if fill_clr else (f(row_bg) if row_bg else PatternFill())
        c.alignment = align(h="center")
        c.border = border()
        ws.row_dimensions[ri].height = 16

    ws.row_dimensions[15].height = 10  # spacer

    # ── Completion Rate ──
    section_title(ws, 16, 2, "  📊  WEEKLY COMPLETION TREND", span=5)
    rate_hdrs = ["Week Of", "Total", "Done", "Missed", "Rate"]
    for ci, h in enumerate(rate_hdrs, 2):
        hdr_cell(ws, 17, ci, h, bg=NAVY)
    ws.row_dimensions[17].height = 18

    rate_rows = [
        ["3/3/26",  25, 24, 1, "96%"],
        ["3/10/26", 25, 23, 2, "92%"],
        ["3/17/26", 25, 22, 3, "88%"],
        ["3/24/26", 25, "—", "—", "—"],
    ]
    for ri, row in enumerate(rate_rows, 18):
        row_bg = SLATE_LIGHT if ri % 2 == 0 else None
        for ci, val in zip(range(2, 7), row):
            body_cell(ws, ri, ci, val, bg=row_bg, h="center")
        rate_val = row[4]
        if rate_val != "—":
            pct    = int(rate_val.strip("%"))
            r_bg   = GREEN_FILL if pct >= 95 else (AMBER_FILL if pct >= 90 else RED_FILL)
            r_tc   = GREEN_TEXT if pct >= 95 else (AMBER_TEXT if pct >= 90 else RED_TEXT)
            c = ws.cell(row=ri, column=6, value=rate_val)
            c.font = font(size=10, bold=True, color=r_tc)
            c.fill = f(r_bg)
            c.alignment = align(h="center")
            c.border = border()
        ws.row_dimensions[ri].height = 16

    ws.row_dimensions[22].height = 10  # spacer

    # ── Quarterly Scorecard Snapshot ──
    section_title(ws, 23, 2, "  ⚙  Q1 SCORECARD SNAPSHOT", span=5)
    sc_hdrs = ["Goal", "Owner", "Target", "Actual", "Status"]
    for ci, h in enumerate(sc_hdrs, 2):
        hdr_cell(ws, 24, ci, h, bg=NAVY)
    ws.row_dimensions[24].height = 18

    sc_rows = [
        ["Work-order backlog < 10",         "D. Singh",   "< 10 open",   "14 open",     "At Risk"],
        ["Vendor invoice on-time ≥ 98%",    "K. Johnson", "98%",         "96.2%",       "At Risk"],
        ["Q1 PM work orders 100% complete", "R. Patel",   "100%",        "91%",         "Behind"],
        ["Zero critical safety incidents",  "J. Carter",  "0 incidents", "0 incidents", "Complete"],
    ]

    status_map = {
        "On Track": (GREEN_FILL, GREEN_TEXT),
        "At Risk":  (AMBER_FILL, AMBER_TEXT),
        "Behind":   (RED_FILL,   RED_TEXT),
        "Complete": (GREY_FILL,  GREY_TEXT),
    }

    for ri, row in enumerate(sc_rows, 25):
        status = row[4]
        row_bg = SLATE_LIGHT if ri % 2 == 0 else None
        for ci, val in zip(range(2, 7), row):
            body_cell(ws, ri, ci, val, bg=row_bg)
        s_bg, s_tc = status_map.get(status, (None, "000000"))
        c = ws.cell(row=ri, column=6, value=status_dot(status))
        c.font = font(size=10, bold=True, color=s_tc)
        c.fill = f(s_bg) if s_bg else PatternFill()
        c.alignment = align(h="center")
        c.border = border()
        ws.row_dimensions[ri].height = 16

    return ws


# ── Tab 2 — Weekly Checklist ──────────────────────────────────────────────────

def build_weekly_checklist(wb):
    ws = wb.create_sheet("Weekly Checklist")
    headers = ["Task", "Owner", "Cadence", "M", "T", "W", "Th", "F", "Flag", "Callout", "Updated"]
    widths  = [40, 16, 12, 5, 5, 5, 5, 5, 10, 38, 11]
    set_col_widths(ws, widths)
    write_header_row(ws, 1, headers)
    ws.freeze_panes = "A2"

    rows = [
        ["Inspect restroom supplies & restock",        "J. Carter",  "Daily",  "✓","✓","✓","✓","✓","Green",  "All floors OK; Bay 3 low — restocked",  "3/21/26"],
        ["Review overnight crew sign-in log",          "M. Torres",  "Daily",  "✓","✓","✓","", "", "Yellow", "Wed crew +22 min late — documented",    "3/20/26"],
        ["Exterior parking lot walk-through",          "D. Singh",   "Daily",  "✓","✓","✓","✓","✓","Green",  "No debris; lighting OK",                "3/21/26"],
        ["Submit vendor invoice approvals to AP",      "K. Johnson", "Weekly", "", "", "", "", "✓","Green",  "3 invoices submitted; 1 credit pending", "3/21/26"],
        ["Verify HVAC filter replacement compliance",  "R. Patel",   "Weekly", "", "", "", "✓","", "Red",    "Unit 4B overdue 2 wks — escalated",     "3/20/26"],
    ]

    for ri, row in enumerate(rows, 2):
        flag   = row[8]
        row_bg = SLATE_LIGHT if ri % 2 == 0 else None
        for ci, val in enumerate(row, 1):
            body_cell(ws, ri, ci, val, bg=row_bg, h="center" if 4 <= ci <= 8 else "left")
        fill_clr = flag_fill(flag)
        tc       = flag_text_color(flag)
        c = ws.cell(row=ri, column=9, value=status_dot(flag))
        c.font = font(size=10, bold=True, color=tc)
        c.fill = f(fill_clr) if fill_clr else (f(row_bg) if row_bg else PatternFill())
        c.alignment = align(h="center")
        c.border = border()
        ws.cell(row=ri, column=11).number_format = DATE_FMT
        ws.row_dimensions[ri].height = 16

    add_dropdown(ws, '"Green,Yellow,Red"', "I2:I100")
    apply_flag_cf(ws, "I", 2, 100)
    ws.sheet_view.showGridLines = False
    return ws


# ── Tab 3 — Adhoc / Projects ──────────────────────────────────────────────────

def build_adhoc(wb):
    ws = wb.create_sheet("Adhoc - Projects")
    headers = ["Initiative", "Owner", "Due Date", "Priority", "Stage", "Flag", "Blocker", "Updated"]
    widths  = [40, 16, 11, 10, 18, 10, 40, 11]
    set_col_widths(ws, widths)
    write_header_row(ws, 1, headers)
    ws.freeze_panes = "A2"

    rows = [
        ["Vendor credentialing portal rollout",    "K. Johnson", "4/15/26", "High",   "In Progress",   "Yellow", "IT integration delayed 2 sprints"],
        ["Q2 janitorial contract renewal",         "M. Torres",  "3/31/26", "High",   "Review Needed", "Red",    "Legal redlines pending since 3/12/26"],
        ["Roof-deck drainage sensors — Bldg C",    "D. Singh",   "5/1/26",  "Medium", "Not Started",   "Green",  ""],
        ["Energy audit — Phase 2",                 "R. Patel",   "6/30/26", "Medium", "In Progress",   "Green",  ""],
        ["Staff training — work-order app",        "J. Carter",  "4/5/26",  "Low",    "Pending",       "Yellow", "Vendor training deck not delivered"],
    ]

    pri_fill = {"High": PRI_HIGH, "Medium": PRI_MED, "Low": PRI_LOW}
    pri_text = {"High": RED_TEXT, "Medium": AMBER_TEXT, "Low": NAVY}

    for ri, row in enumerate(rows, 2):
        flag     = row[5]
        priority = row[3]
        row_bg   = SLATE_LIGHT if ri % 2 == 0 else None
        for ci, val in enumerate(row, 1):
            body_cell(ws, ri, ci, val, bg=row_bg)
        ws.cell(row=ri, column=3).number_format = DATE_FMT
        # Priority chip
        c = ws.cell(row=ri, column=4, value=priority)
        c.font = font(size=10, bold=True, color=pri_text.get(priority, "000000"))
        c.fill = f(pri_fill.get(priority, row_bg or WHITE))
        c.alignment = align(h="center")
        c.border = border()
        # Flag cell
        fill_clr = flag_fill(flag)
        tc       = flag_text_color(flag)
        c2 = ws.cell(row=ri, column=6, value=status_dot(flag))
        c2.font = font(size=10, bold=True, color=tc)
        c2.fill = f(fill_clr) if fill_clr else (f(row_bg) if row_bg else PatternFill())
        c2.alignment = align(h="center")
        c2.border = border()
        ws.cell(row=ri, column=8, value="3/21/26").number_format = DATE_FMT
        ws.row_dimensions[ri].height = 16

    add_dropdown(ws, '"High,Medium,Low"', "D2:D100")
    add_dropdown(ws, '"Not Started,In Progress,Pending,Review Needed,Complete"', "E2:E100")
    add_dropdown(ws, '"Green,Yellow,Red"', "F2:F100")
    apply_flag_cf(ws, "F", 2, 100)
    ws.sheet_view.showGridLines = False
    return ws


# ── Tab 4 — Quarterly Scorecard ───────────────────────────────────────────────

def build_scorecard(wb):
    ws = wb.create_sheet("Quarterly Scorecard")
    headers = ["Goal", "Owner", "Target", "Actual", "Status", "Callout"]
    widths  = [44, 16, 18, 18, 14, 48]
    set_col_widths(ws, widths)
    write_header_row(ws, 1, headers)
    ws.freeze_panes = "A2"

    rows = [
        ["Reduce work-order backlog to < 10",        "D. Singh",   "< 10 open",   "14 open",     "At Risk",  "Backlog spiked — 2 emergency repairs; targeting Apr 1 clearance"],
        ["Achieve 98% vendor invoice on-time rate",  "K. Johnson", "98%",         "96.2%",       "At Risk",  "3 invoices on hold; AP process update underway"],
        ["Complete all Q1 scheduled PM work orders", "R. Patel",   "100%",        "91%",         "Behind",   "HVAC 4B + roof drains deferred → Apr"],
        ["Zero critical safety incidents",           "J. Carter",  "0 incidents", "0 incidents", "Complete", "Q1 closed clean; near-miss log current"],
    ]

    status_map = {
        "On Track": (GREEN_FILL, GREEN_TEXT),
        "At Risk":  (AMBER_FILL, AMBER_TEXT),
        "Behind":   (RED_FILL,   RED_TEXT),
        "Complete": (GREY_FILL,  GREY_TEXT),
    }

    for ri, row in enumerate(rows, 2):
        status = row[4]
        row_bg = SLATE_LIGHT if ri % 2 == 0 else None
        for ci, val in enumerate(row, 1):
            body_cell(ws, ri, ci, val, bg=row_bg, wrap=(ci == 6))
        s_bg, s_tc = status_map.get(status, (None, "000000"))
        c = ws.cell(row=ri, column=5, value=status_dot(status))
        c.font = font(size=10, bold=True, color=s_tc)
        c.fill = f(s_bg) if s_bg else PatternFill()
        c.alignment = align(h="center")
        c.border = border()
        ws.row_dimensions[ri].height = 16

    add_dropdown(ws, '"On Track,At Risk,Behind,Complete"', "E2:E100")
    ws.sheet_view.showGridLines = False
    return ws


# ── Tab 5 — Accountability Log ────────────────────────────────────────────────

def build_accountability(wb):
    ws = wb.create_sheet("Accountability Log")
    headers = ["Date", "Task", "Owner", "Due Date", "Misses", "Root Cause", "Resolution", "Resolved"]
    widths  = [11, 36, 16, 11, 8, 36, 40, 11]
    set_col_widths(ws, widths)

    for ci, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=ci, value=h)
        c.font = font(size=10, bold=True, color=WHITE)
        c.fill = f(DEEP_RED)
        c.alignment = align(h="center")
        c.border = border()
    ws.row_dimensions[1].height = 20
    ws.freeze_panes = "A2"

    rows = [
        ["3/10/26", "Submit Q1 PM completion report",              "R. Patel",  "3/7/26",  2, "Vendor did not provide service logs on time",        "Logs obtained manually; submitted with director approval", "3/10/26"],
        ["3/18/26", "Renew janitorial contract before expiration", "M. Torres", "3/15/26", 1, "Legal redlines not returned within 5-day window",    "Escalated to legal director; interim extension executed",  ""],
        ["3/21/26", "HVAC filter replacement — Unit 4B",           "D. Singh",  "3/7/26",  3, "Parts backordered; no approved substitute available", "Emergency PO issued; rescheduled",                        ""],
    ]

    for ri, row in enumerate(rows, 2):
        row_bg = SLATE_LIGHT if ri % 2 == 0 else None
        for ci, val in enumerate(row, 1):
            body_cell(ws, ri, ci, val, bg=row_bg)
        ws.cell(row=ri, column=1).number_format = DATE_FMT
        ws.cell(row=ri, column=4).number_format = DATE_FMT
        ws.cell(row=ri, column=8).number_format = DATE_FMT
        miss = row[4]
        c = ws.cell(row=ri, column=5, value=miss)
        c.font = font(size=10, bold=(miss > 1), color=RED_TEXT if miss > 1 else "000000")
        c.alignment = align(h="center")
        c.border = border()
        if row_bg:
            c.fill = f(row_bg)
        ws.row_dimensions[ri].height = 16

    ws.sheet_view.showGridLines = False
    return ws


# ── Main builder ──────────────────────────────────────────────────────────────

def build_workbook(output_path):
    wb = Workbook()
    wb.remove(wb.active)

    build_dashboard(wb)
    build_weekly_checklist(wb)
    build_adhoc(wb)
    build_scorecard(wb)
    build_accountability(wb)

    wb.save(output_path)
    print(f"[✓] Saved: {output_path}")
    return output_path


# ── OneDrive Upload ───────────────────────────────────────────────────────────

GRAPH_SCOPE     = "Files.ReadWrite offline_access"
DEVICE_CODE_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/devicecode"
TOKEN_URL       = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
UPLOAD_URL      = "https://graph.microsoft.com/v1.0/me/drive/root:/MDF_Operations_Tracker.xlsx:/content"
CLIENT_ID       = "14d82eec-204b-4c2f-b7e8-296a70dab67e"


def device_code_flow():
    r = requests.post(DEVICE_CODE_URL, data={"client_id": CLIENT_ID, "scope": GRAPH_SCOPE})
    r.raise_for_status()
    dc = r.json()

    print("\n" + "="*60)
    print("Microsoft Authentication Required")
    print("="*60)
    print(f"  1. Open:  {dc['verification_uri']}")
    print(f"  2. Enter code: {dc['user_code']}")
    print("="*60)
    print("Waiting for sign-in…\n")

    import time
    interval = int(dc.get("interval", 5))
    device_code = dc["device_code"]

    while True:
        time.sleep(interval)
        resp = requests.post(TOKEN_URL, data={
            "client_id": CLIENT_ID,
            "grant_type": "urn:ietf:params:oauth2:grant-type:device_code",
            "device_code": device_code,
        })
        token_data = resp.json()
        if "access_token" in token_data:
            print("[✓] Authentication successful.")
            return token_data["access_token"]
        error = token_data.get("error", "")
        if error == "authorization_pending":
            continue
        elif error == "slow_down":
            interval += 5
        else:
            print(f"[✗] Auth error: {token_data.get('error_description', token_data)}")
            sys.exit(1)


def upload_to_onedrive(file_path, access_token):
    with open(file_path, "rb") as fh:
        content = fh.read()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    resp = requests.put(UPLOAD_URL, headers=headers, data=content)
    if resp.status_code in (200, 201):
        web_url = resp.json().get("webUrl", "(URL not returned)")
        print(f"\n[✓] Uploaded to OneDrive.\n    {web_url}\n")
        return web_url
    else:
        print(f"[✗] Upload failed ({resp.status_code}): {resp.text}")
        sys.exit(1)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    output_path = os.path.join(os.path.dirname(__file__), "MDF_Operations_Tracker.xlsx")

    build_workbook(output_path)

    token = os.environ.get("ONEDRIVE_ACCESS_TOKEN")
    if token:
        print("[i] Using ONEDRIVE_ACCESS_TOKEN env var.")
    else:
        print("[i] No token found — starting device code flow.")
        token = device_code_flow()

    upload_to_onedrive(output_path, token)
