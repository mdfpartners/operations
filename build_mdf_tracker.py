"""
MDF Operations Tracker — Excel builder + OneDrive upload
"""

import os
import sys
import requests
from openpyxl import Workbook
from openpyxl.styles import (
    PatternFill, Font, Alignment, Border, Side, numbers
)
from openpyxl.styles.differential import DifferentialStyle
from openpyxl.formatting.rule import Rule, DataBarRule, ColorScaleRule
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule, FormulaRule

# ── Palette ───────────────────────────────────────────────────────────────────
DARK_HEADER   = "1F3864"   # dark navy
WHITE         = "FFFFFF"
GREEN_FILL    = "C6EFCE"
YELLOW_FILL   = "FFEB9C"
RED_FILL      = "FFC7CE"
ALT_ROW       = "EBF0F8"   # light blue-grey alternating row
STATUS_ONTK   = "C6EFCE"
STATUS_RISK   = "FFEB9C"
STATUS_BEHIND = "FFC7CE"
STATUS_DONE   = "D9D9D9"
FONT_NAME     = "Calibri"
FONT_SIZE     = 11

# ── Helpers ───────────────────────────────────────────────────────────────────

def header_font(bold=True, color=WHITE):
    return Font(name=FONT_NAME, size=FONT_SIZE, bold=bold, color=color)

def body_font(bold=False):
    return Font(name=FONT_NAME, size=FONT_SIZE, bold=bold)

def hdr_fill(hex_color=DARK_HEADER):
    return PatternFill("solid", fgColor=hex_color)

def solid_fill(hex_color):
    return PatternFill("solid", fgColor=hex_color)

def thin_border():
    s = Side(style="thin", color="BFBFBF")
    return Border(left=s, right=s, top=s, bottom=s)

def write_headers(ws, headers, col_widths=None):
    for ci, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=ci, value=h)
        cell.font = header_font()
        cell.fill = hdr_fill()
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border()
    ws.row_dimensions[1].height = 22
    if col_widths:
        for ci, w in enumerate(col_widths, 1):
            ws.column_dimensions[get_column_letter(ci)].width = w

def apply_alt_rows(ws, start_row, end_row, num_cols):
    for r in range(start_row, end_row + 1):
        fill = solid_fill(ALT_ROW) if r % 2 == 0 else None
        for c in range(1, num_cols + 1):
            cell = ws.cell(row=r, column=c)
            cell.font = body_font()
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            cell.border = thin_border()
            if fill:
                cell.fill = fill

def add_flag_validation(ws, col_letter, start_row, end_row):
    dv = DataValidation(
        type="list",
        formula1='"Green,Yellow,Red"',
        allow_blank=True,
        showErrorMessage=True,
        errorTitle="Invalid",
        error="Choose Green, Yellow, or Red"
    )
    dv.sqref = f"{col_letter}{start_row}:{col_letter}{end_row}"
    ws.add_data_validation(dv)

def add_flag_cf(ws, col_letter, start_row, end_row):
    rng = f"{col_letter}{start_row}:{col_letter}{end_row}"
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"Green"'], fill=solid_fill(GREEN_FILL)))
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"Yellow"'], fill=solid_fill(YELLOW_FILL)))
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"Red"'], fill=solid_fill(RED_FILL)))

def write_row(ws, row_num, values):
    for ci, v in enumerate(values, 1):
        ws.cell(row=row_num, column=ci, value=v)

# ── Tab 1 — Weekly Checklist ──────────────────────────────────────────────────

def build_weekly_checklist(wb):
    ws = wb.create_sheet("Weekly Checklist")
    headers = ["Task", "Owner", "Cadence", "Mon", "Tue", "Wed", "Thu", "Fri",
               "Flag", "Notes", "Last Updated"]
    widths  = [38, 18, 14, 7, 7, 7, 7, 7, 10, 40, 15]
    write_headers(ws, headers, widths)
    ws.freeze_panes = "A2"

    rows = [
        ["Inspect restroom supplies and restock as needed",        "J. Carter",  "Daily",  "✓","✓","✓","✓","✓","Green", "All floors checked; Bay 3 low on paper towels", "2026-03-21"],
        ["Review overnight cleaning crew sign-in log",             "M. Torres",  "Daily",  "✓","✓","✓","","", "Yellow","Wed crew clocked in 22 min late — noted",          "2026-03-20"],
        ["Conduct exterior parking lot walk-through",               "D. Singh",   "Daily",  "✓","✓","✓","✓","✓","Green", "No debris; lighting functioning",                   "2026-03-21"],
        ["Submit weekly vendor invoice approvals to AP",           "K. Johnson", "Weekly", "","","","","✓", "Green", "3 invoices submitted Fri; 1 pending credit memo",   "2026-03-21"],
        ["Verify HVAC filter replacement schedule compliance",     "R. Patel",   "Weekly", "","","","✓","",  "Red",  "Unit 4B filter overdue by 2 weeks — escalated",     "2026-03-20"],
    ]

    for ri, row in enumerate(rows, 2):
        write_row(ws, ri, row)

    apply_alt_rows(ws, 2, len(rows) + 1, len(headers))
    add_flag_validation(ws, "I", 2, 100)
    add_flag_cf(ws, "I", 2, 100)
    ws.sheet_view.showGridLines = True
    return ws

# ── Tab 2 — Adhoc / Projects ──────────────────────────────────────────────────

def build_adhoc(wb):
    ws = wb.create_sheet("Adhoc - Projects")
    headers = ["Initiative", "Owner", "Due Date", "Priority", "Stage",
               "Flag", "Blockers", "Notes", "Last Updated"]
    widths  = [38, 18, 13, 12, 16, 10, 34, 60, 15]
    write_headers(ws, headers, widths)
    ws.freeze_panes = "A2"

    rows = [
        ["Roll out new vendor credentialing portal",    "K. Johnson", "2026-04-15", "High",   "In Progress",    "Yellow",
         "IT integration delayed by 2 sprints",
         "[2026-03-10] Kickoff complete\n[2026-03-18] IT timeline revised to Apr 15", "2026-03-21"],
        ["Negotiate Q2 janitorial contract renewal",   "M. Torres",  "2026-03-31", "High",   "Review Needed",  "Red",
         "Legal redlines outstanding since Mar 12",
         "[2026-03-01] RFP sent to 3 vendors\n[2026-03-14] Legal review in progress", "2026-03-20"],
        ["Install roof-deck drainage sensors, Bldg C", "D. Singh",   "2026-05-01", "Medium", "Not Started",    "Green",
         "",
         "[2026-03-05] Budget approved\n[2026-03-19] Scope finalized with contractor", "2026-03-19"],
        ["Implement energy audit recommendations",     "R. Patel",   "2026-06-30", "Medium", "In Progress",    "Green",
         "",
         "[2026-02-20] Phase 1 LED swap complete — 18% reduction\n[2026-03-15] Phase 2 scoped", "2026-03-15"],
        ["Train facility staff on new work-order app", "J. Carter",  "2026-04-05", "Low",    "Pending",        "Yellow",
         "Waiting on vendor to finalize training deck",
         "[2026-03-12] Pilot session scheduled\n[2026-03-21] Deck still pending from vendor", "2026-03-21"],
    ]

    for ri, row in enumerate(rows, 2):
        write_row(ws, ri, row)
        ws.cell(row=ri, column=3).number_format = "YYYY-MM-DD"
        ws.cell(row=ri, column=9).number_format = "YYYY-MM-DD"
        ws.cell(row=ri, column=8).alignment = Alignment(wrap_text=True, vertical="top")

    apply_alt_rows(ws, 2, len(rows) + 1, len(headers))

    # Priority dropdown
    dv_pri = DataValidation(type="list", formula1='"High,Medium,Low"', allow_blank=True)
    dv_pri.sqref = "D2:D100"
    ws.add_data_validation(dv_pri)

    # Stage dropdown
    dv_stage = DataValidation(type="list",
        formula1='"Not Started,In Progress,Pending,Review Needed,Complete"', allow_blank=True)
    dv_stage.sqref = "E2:E100"
    ws.add_data_validation(dv_stage)

    add_flag_validation(ws, "F", 2, 100)
    add_flag_cf(ws, "F", 2, 100)
    return ws

# ── Tab 3 — Quarterly Scorecard ───────────────────────────────────────────────

def build_scorecard(wb):
    ws = wb.create_sheet("Quarterly Scorecard")
    headers = ["Goal", "Owner", "Target", "Actual", "Status", "Notes"]
    widths  = [44, 18, 18, 18, 16, 50]
    write_headers(ws, headers, widths)
    ws.freeze_panes = "A2"

    rows = [
        ["Reduce work-order backlog to < 10 open items",  "D. Singh",   "< 10 open",    "14 open",     "At Risk",  "Backlog spiked after 2 emergency repairs in Feb; targeting clearance by Apr 1"],
        ["Achieve 98% vendor invoice on-time payment",    "K. Johnson", "98%",           "96.2%",       "At Risk",  "3 invoices held pending PO correction; AP process update underway"],
        ["Complete all Q1 scheduled PM work orders",      "R. Patel",   "100% complete", "91% complete","Behind",   "HVAC unit 4B and roof drain units deferred; rescheduled for Apr"],
        ["Zero critical safety incidents across all sites","J. Carter",  "0 incidents",   "0 incidents", "Complete", "Q1 closed with clean record; near-miss log reviewed monthly"],
    ]

    for ri, row in enumerate(rows, 2):
        write_row(ws, ri, row)

    apply_alt_rows(ws, 2, len(rows) + 1, len(headers))

    # Status dropdown
    dv_status = DataValidation(type="list",
        formula1='"On Track,At Risk,Behind,Complete"', allow_blank=True)
    dv_status.sqref = "E2:E100"
    ws.add_data_validation(dv_status)

    # Conditional formatting on Status (col E)
    rng = "E2:E100"
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"On Track"'], fill=solid_fill(STATUS_ONTK)))
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"At Risk"'],  fill=solid_fill(STATUS_RISK)))
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"Behind"'],   fill=solid_fill(STATUS_BEHIND)))
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"Complete"'], fill=solid_fill(STATUS_DONE)))
    return ws

# ── Tab 4 — Accountability Log ────────────────────────────────────────────────

def build_accountability(wb):
    ws = wb.create_sheet("Accountability Log")
    headers = ["Date", "Task", "Owner", "Original Due Date", "Miss Count",
               "Reason", "Resolution", "Resolved Date"]
    widths  = [13, 38, 18, 18, 12, 40, 44, 15]

    # Red header fill for escalation signal
    for ci, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=ci, value=h)
        cell.font = header_font(color=WHITE)
        cell.fill = solid_fill("C00000")  # deep red
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border()
    ws.row_dimensions[1].height = 22
    for ci, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(ci)].width = w

    ws.freeze_panes = "A2"

    rows = [
        ["2026-03-10", "Submit Q1 PM completion report",               "R. Patel",   "2026-03-07", 2,
         "Data collection delayed; vendor did not provide service logs on time",
         "Logs obtained manually; report submitted Mar 10 with director approval", "2026-03-10"],
        ["2026-03-18", "Renew janitorial contract before expiration",  "M. Torres",  "2026-03-15", 1,
         "Legal redlines not returned within agreed 5-day window",
         "Escalated to legal director; interim extension executed",              ""],
        ["2026-03-21", "Complete HVAC filter replacement — Unit 4B",   "D. Singh",   "2026-03-07", 3,
         "Parts backordered from supplier; no substitute approved",
         "Emergency PO issued for alternate supplier; work order rescheduled",  ""],
    ]

    for ri, row in enumerate(rows, 2):
        write_row(ws, ri, row)
        ws.cell(row=ri, column=1).number_format = "YYYY-MM-DD"
        ws.cell(row=ri, column=4).number_format = "YYYY-MM-DD"
        ws.cell(row=ri, column=8).number_format = "YYYY-MM-DD"
        ws.cell(row=ri, column=5).number_format = "0"

    apply_alt_rows(ws, 2, len(rows) + 1, len(headers))
    return ws

# ── Tab 5 — Dashboard ─────────────────────────────────────────────────────────

def build_dashboard(wb):
    ws = wb.create_sheet("Dashboard")
    ws.sheet_view.showGridLines = False

    def section_header(row, text):
        cell = ws.cell(row=row, column=1, value=text)
        cell.font = Font(name=FONT_NAME, size=13, bold=True, color=DARK_HEADER)
        cell.alignment = Alignment(vertical="center")

    def table_header(row, col, value):
        cell = ws.cell(row=row, column=col, value=value)
        cell.font = header_font()
        cell.fill = hdr_fill()
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border()

    def table_cell(row, col, value, bold=False, align="left"):
        cell = ws.cell(row=row, column=col, value=value)
        cell.font = Font(name=FONT_NAME, size=FONT_SIZE, bold=bold)
        cell.alignment = Alignment(horizontal=align, vertical="center")
        cell.border = thin_border()
        return cell

    # Column widths
    col_widths = [30, 22, 22, 22, 22, 20]
    for ci, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(ci)].width = w

    # ── Section 1: Flags Summary ──
    section_header(1, "⚑  Open Flags — Red & Yellow (Standup View)")
    ws.row_dimensions[1].height = 24

    flag_headers = ["Source", "Task / Initiative", "Owner", "Flag", "Notes"]
    for ci, h in enumerate(flag_headers, 1):
        table_header(2, ci, h)

    flag_rows = [
        ["Pull from Weekly",  "Review overnight cleaning crew sign-in log",        "M. Torres",  "Yellow", "Wed crew clocked in late"],
        ["Pull from Weekly",  "Verify HVAC filter replacement schedule compliance", "R. Patel",   "Red",    "Unit 4B overdue — escalated"],
        ["Pull from Adhoc",   "Roll out new vendor credentialing portal",           "K. Johnson", "Yellow", "IT integration delayed"],
        ["Pull from Adhoc",   "Negotiate Q2 janitorial contract renewal",           "M. Torres",  "Red",    "Legal redlines outstanding"],
        ["Pull from Adhoc",   "Train facility staff on new work-order app",         "J. Carter",  "Yellow", "Waiting on vendor training deck"],
    ]

    for ri, row in enumerate(flag_rows, 3):
        fill = solid_fill(RED_FILL) if row[3] == "Red" else solid_fill(YELLOW_FILL)
        for ci, val in enumerate(row, 1):
            c = table_cell(ri, ci, val)
            if ri % 2 == 0:
                c.fill = solid_fill(ALT_ROW)
        ws.cell(row=ri, column=4).fill = fill  # override flag cell

    # ── Section 2: Bench Scorecard ──
    section_header(10, "⚙  Bench Scorecard — Vetted Substitutes")
    ws.row_dimensions[10].height = 24

    bench_headers = ["Market", "Vetted Subs", "Warm Candidates", "Last Updated"]
    for ci, h in enumerate(bench_headers, 1):
        table_header(11, ci, h)

    bench_rows = [
        ["Northeast",    4, 2, "2026-03-15"],
        ["Mid-Atlantic", 3, 1, "2026-03-10"],
        ["Southeast",    5, 3, "2026-03-18"],
        ["Midwest",      2, 0, "2026-03-01"],
    ]
    for ri, row in enumerate(bench_rows, 12):
        for ci, val in enumerate(row, 1):
            c = table_cell(ri, ci, val, align="center")
            if ri % 2 == 0:
                c.fill = solid_fill(ALT_ROW)

    # ── Section 3: Week Completion Rate ──
    section_header(18, "📊  Week Completion Rate")
    ws.row_dimensions[18].height = 24

    rate_headers = ["Week Of", "Total Tasks", "Completed", "Missed", "Rate %"]
    for ci, h in enumerate(rate_headers, 1):
        table_header(19, ci, h)

    rate_rows = [
        ["2026-03-03", 25, 24, 1, "96%"],
        ["2026-03-10", 25, 23, 2, "92%"],
        ["2026-03-17", 25, 22, 3, "88%"],
        ["2026-03-24", 25, "-", "-", "—"],
    ]
    for ri, row in enumerate(rate_rows, 20):
        for ci, val in enumerate(row, 1):
            c = table_cell(ri, ci, val, align="center")
            if ri % 2 == 0:
                c.fill = solid_fill(ALT_ROW)

    return ws

# ── Main builder ──────────────────────────────────────────────────────────────

def build_workbook(output_path):
    wb = Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    build_weekly_checklist(wb)
    build_adhoc(wb)
    build_scorecard(wb)
    build_accountability(wb)
    build_dashboard(wb)

    wb.save(output_path)
    print(f"[✓] Saved: {output_path}")
    return output_path

# ── OneDrive Upload ───────────────────────────────────────────────────────────

GRAPH_SCOPE    = "Files.ReadWrite offline_access"
DEVICE_CODE_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/devicecode"
TOKEN_URL       = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
UPLOAD_URL      = "https://graph.microsoft.com/v1.0/me/drive/root:/MDF_Operations_Tracker.xlsx:/content"
# Public MSAL-style client id used for device-code flows in MS docs examples
CLIENT_ID       = "14d82eec-204b-4c2f-b7e8-296a70dab67e"  # MS Graph Explorer public client


def device_code_flow():
    """Authenticate via device-code flow and return an access token."""
    r = requests.post(DEVICE_CODE_URL, data={
        "client_id": CLIENT_ID,
        "scope": GRAPH_SCOPE,
    })
    r.raise_for_status()
    dc = r.json()

    print("\n" + "="*60)
    print("Microsoft Authentication Required")
    print("="*60)
    print(f"  1. Open:  {dc['verification_uri']}")
    print(f"  2. Enter code: {dc['user_code']}")
    print("="*60)
    print("Waiting for you to complete sign-in…\n")

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
    """Upload file to OneDrive root and return the web URL."""
    with open(file_path, "rb") as f:
        content = f.read()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    resp = requests.put(UPLOAD_URL, headers=headers, data=content)

    if resp.status_code in (200, 201):
        item = resp.json()
        web_url = item.get("webUrl", "(URL not returned)")
        print(f"\n[✓] Uploaded to OneDrive successfully.")
        print(f"    Shareable link: {web_url}\n")
        return web_url
    else:
        print(f"[✗] Upload failed ({resp.status_code}): {resp.text}")
        sys.exit(1)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    output_path = os.path.join(os.path.dirname(__file__), "MDF_Operations_Tracker.xlsx")

    # Step 1 — Build the Excel file
    build_workbook(output_path)

    # Step 2 — Authenticate & upload
    token = os.environ.get("ONEDRIVE_ACCESS_TOKEN")
    if token:
        print("[i] Using access token from ONEDRIVE_ACCESS_TOKEN env var.")
    else:
        print("[i] No ONEDRIVE_ACCESS_TOKEN found — starting device code flow.")
        token = device_code_flow()

    upload_to_onedrive(output_path, token)
