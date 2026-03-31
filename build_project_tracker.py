#!/usr/bin/env python3
"""
Build MDF_Project_Tracker.xlsm with CloseItem (Ctrl+Shift+C) and InsertRow (Ctrl+Shift+R) macros.
"""
import os, struct, zipfile, shutil, re
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ── Palette ───────────────────────────────────────────────────────────────────
NAVY        = "00338D"
WHITE       = "FFFFFF"
SLATE_LIGHT = "F4F6FA"
BORDER_CLR  = "CBD4E1"

ACTIVE_HDR  = "00338D"; ACTIVE_ROW  = "EBF3FB"; ACTIVE_ACC  = "00338D"
HOLD_HDR    = "E65100"; HOLD_ROW    = "FFF8E1"; HOLD_ACC    = "E65100"
BLOCKED_HDR = "B71C1C"; BLOCKED_ROW = "FDECEA"; BLOCKED_ACC = "B71C1C"

CLOSED_HDR  = "546E7A"
FONT_NAME   = "Calibri"
DATE_FMT    = "M/D/YY"

def fill(hex_color):
    return PatternFill("solid", fgColor=hex_color)

def bdr(color=BORDER_CLR, left_color=None, left_style="thin"):
    s = Side(style="thin", color=color)
    l = Side(style=left_style, color=left_color or color)
    return Border(left=l, right=s, top=s, bottom=s)

def font(size=10, bold=False, color="000000"):
    return Font(name=FONT_NAME, size=size, bold=bold, color=color)

def align(h="left", v="center", wrap=False):
    return Alignment(horizontal=h, vertical=v, wrap_text=wrap)

# ── VBA Source Code ───────────────────────────────────────────────────────────
TW_SRC = (
    'Attribute VB_Name = "ThisWorkbook"\r\n'
    'Attribute VB_Base = "0{00020819-0000-0000-C000-000000000046}"\r\n'
    'Attribute VB_GlobalNameSpace = False\r\n'
    'Attribute VB_Creatable = False\r\n'
    'Attribute VB_PredeclaredId = True\r\n'
    'Attribute VB_Exposed = True\r\n'
    '\r\n'
    'Private Sub Workbook_Open()\r\n'
    '    Application.OnKey "^+C", "CloseItem"\r\n'
    '    Application.OnKey "^+R", "InsertRow"\r\n'
    'End Sub\r\n'
    '\r\n'
    'Private Sub Workbook_BeforeClose(Cancel As Boolean)\r\n'
    '    Application.OnKey "^+C"\r\n'
    '    Application.OnKey "^+R"\r\n'
    'End Sub\r\n'
)

M1_SRC = (
    'Attribute VB_Name = "Module1"\r\n'
    '\r\n'
    'Option Explicit\r\n'
    '\r\n'
    "' Returns True for: row 1 (col headers), blank spacer rows,\r\n"
    "' and lane-header rows (merged across 3+ cols).\r\n"
    'Function IsNonDataRow(ws As Worksheet, r As Long) As Boolean\r\n'
    '    If r <= 1 Then IsNonDataRow = True: Exit Function\r\n'
    '    Dim c As Long, blank As Boolean\r\n'
    '    blank = True\r\n'
    '    For c = 1 To 15\r\n'
    '        If Trim(CStr(ws.Cells(r, c).Value)) <> "" Then\r\n'
    '            blank = False: Exit For\r\n'
    '        End If\r\n'
    '    Next c\r\n'
    '    If blank Then IsNonDataRow = True: Exit Function\r\n'
    '    If ws.Cells(r, 1).MergeArea.Columns.Count >= 3 Then\r\n'
    '        IsNonDataRow = True: Exit Function\r\n'
    '    End If\r\n'
    '    IsNonDataRow = False\r\n'
    'End Function\r\n'
    '\r\n'
    "' CloseItem - Ctrl+Shift+C\r\n"
    'Sub CloseItem()\r\n'
    '    Dim ws       As Worksheet\r\n'
    '    Dim closedWs As Worksheet\r\n'
    '    Dim r        As Long\r\n'
    '    Dim lastR    As Long\r\n'
    '    Set ws = ActiveSheet\r\n'
    '    If ws.Name <> "Project Tracker" And ws.Name <> "Open Items" Then\r\n'
    "        MsgBox \"CloseItem works on 'Project Tracker' or 'Open Items' only.\", vbInformation\r\n"
    '        Exit Sub\r\n'
    '    End If\r\n'
    '    r = ActiveCell.Row\r\n'
    '    If IsNonDataRow(ws, r) Then\r\n'
    '        MsgBox "Please select a project or item row.", vbExclamation\r\n'
    '        Exit Sub\r\n'
    '    End If\r\n'
    '    Set closedWs = ThisWorkbook.Sheets("Closed")\r\n'
    '    lastR = closedWs.Cells(closedWs.Rows.Count, 2).End(xlUp).Row + 1\r\n'
    '    If lastR < 2 Then lastR = 2\r\n'
    '    ws.Rows(r).Copy\r\n'
    '    closedWs.Rows(lastR).PasteSpecial Paste:=xlPasteAllUsingSourceTheme\r\n'
    '    Application.CutCopyMode = False\r\n'
    '    closedWs.Cells(lastR, 3).Value = Date\r\n'
    '    closedWs.Cells(lastR, 3).NumberFormat = "M/D/YY"\r\n'
    '    ws.Rows(r).Delete Shift:=xlShiftUp\r\n'
    'End Sub\r\n'
    '\r\n'
    "' InsertRow - Ctrl+Shift+R\r\n"
    'Sub InsertRow()\r\n'
    '    Dim ws      As Worksheet\r\n'
    '    Dim r       As Long\r\n'
    '    Dim insertR As Long\r\n'
    '    Dim maxR    As Long\r\n'
    '    Dim i       As Long\r\n'
    '    Set ws = ActiveSheet\r\n'
    '    r = ActiveCell.Row\r\n'
    '    If r < 2 Or IsNonDataRow(ws, r) Then\r\n'
    '        MsgBox "Please select a cell in a data section.", vbExclamation\r\n'
    '        Exit Sub\r\n'
    '    End If\r\n'
    '    maxR = ws.Cells(ws.Rows.Count, 2).End(xlUp).Row\r\n'
    '    insertR = maxR + 1\r\n'
    '    For i = r + 1 To maxR\r\n'
    '        If IsNonDataRow(ws, i) Then\r\n'
    '            insertR = i\r\n'
    '            Exit For\r\n'
    '        End If\r\n'
    '    Next i\r\n'
    '    ws.Rows(insertR).Insert Shift:=xlShiftDown\r\n'
    '    ws.Rows(insertR - 1).Copy\r\n'
    '    ws.Rows(insertR).PasteSpecial Paste:=xlPasteFormats\r\n'
    '    Application.CutCopyMode = False\r\n'
    '    ws.Rows(insertR).ClearContents\r\n'
    '    ws.Cells(insertR, 2).Select\r\n'
    'End Sub\r\n'
)

# ── MS-OVBA Compression (uncompressed-chunk variant) ─────────────────────────
def compress_vba(data: bytes) -> bytes:
    out = bytearray([0x01])          # SignatureByte
    i = 0
    while i < len(data):
        chunk = data[i:i + 4096]
        # Header: bits[0:11]=size-1, bit[15]=0 (uncompressed)
        out += struct.pack('<H', len(chunk) - 1) + chunk
        i += 4096
    return bytes(out)

# ── VBA dir stream ────────────────────────────────────────────────────────────
def build_dir_stream(modules) -> bytes:
    """Build and compress the MS-OVBA dir stream."""
    def rec(id_, data=b''):
        return struct.pack('<HI', id_, len(data)) + data
    u16 = lambda v: struct.pack('<H', v)
    u32 = lambda v: struct.pack('<I', v)

    buf = bytearray()
    buf += rec(0x0001, u32(0x00000001))          # PROJECTSYSKIND  Win32
    buf += rec(0x0002, u32(0x00000409))          # PROJECTLCID
    buf += rec(0x0014, u32(0x00000409))          # PROJECTLCIDINVOKE
    buf += rec(0x0003, u16(0x04E4))              # PROJECTCODEPAGE 1252
    buf += rec(0x0004, b'VBAProject')            # PROJECTNAME
    buf += struct.pack('<HI', 0x0005, 0)         # PROJECTDOCSTRING (empty)
    buf += struct.pack('<HI', 0x0040, 0)         # PROJECTDOCSTRING unicode
    buf += struct.pack('<HI', 0x0006, 0)         # PROJECTHELPFILEPATH1
    buf += struct.pack('<HI', 0x003D, 0)         # PROJECTHELPFILEPATH2
    buf += rec(0x0007, u32(0x00000000))          # PROJECTHELPCONTEXT
    buf += rec(0x0008, u32(0x00000000))          # PROJECTLIBFLAGS
    # PROJECTVERSION: special layout (Reserved=4 is not a size)
    buf += struct.pack('<HIIH', 0x0009, 0x00000004, 0x75A70000, 0x000D)
    buf += struct.pack('<HI', 0x000C, 0)         # PROJECTCONSTANTS
    buf += struct.pack('<HI', 0x003C, 0)         # PROJECTCONSTANTS unicode
    # PROJECTMODULES
    buf += rec(0x000F, u16(len(modules)))        # count
    buf += rec(0x0013, u16(0xFFFF))              # PROJECTCOOKIE

    for m in modules:
        name     = m['name'].encode('cp1252')
        name_uni = m['name'].encode('utf-16-le')
        sname    = m['stream'].encode('cp1252')
        sname_uni = m['stream'].encode('utf-16-le')
        mtype    = m.get('type', 0x0021)
        offset   = m.get('offset', 0)

        buf += rec(0x0019, name)                 # MODULENAME
        buf += rec(0x0047, name_uni)             # MODULENAME unicode
        # MODULESTREAMNAME + unicode inline
        buf += struct.pack('<HI', 0x001A, len(sname)) + sname
        buf += struct.pack('<HI', 0x0032, len(sname_uni)) + sname_uni
        buf += struct.pack('<HI', 0x001C, 0)     # MODULEDOCSTRING
        buf += struct.pack('<HI', 0x0048, 0)     # MODULEDOCSTRING unicode
        buf += rec(0x0031, u32(offset))          # MODULEOFFSET (TextOffset)
        buf += rec(0x001E, u32(0x00000000))      # MODULEHELPCONTEXT
        buf += rec(0x002C, u16(0xFFFF))          # MODULECOOKIE
        buf += struct.pack('<HI', mtype, 0)      # MODULETYPE (no data)
        buf += struct.pack('<HI', 0x002B, 0)     # TERMINATOR

    return compress_vba(bytes(buf))

# ── Compound File Binary writer ───────────────────────────────────────────────
ENDOFCHAIN = 0xFFFFFFFE
FATSECT    = 0xFFFFFFFD
FREESECT   = 0xFFFFFFFF
SECTOR_SZ  = 512

def pad_sector(data: bytes) -> bytes:
    r = len(data) % SECTOR_SZ
    return data if r == 0 else data + b'\x00' * (SECTOR_SZ - r)

def dir_entry(name, etype, color, left, right, child, clsid, start, size):
    e = bytearray(128)
    if name:
        enc = name.encode('utf-16-le')
        e[0:min(len(enc), 62)] = enc[:62]
        struct.pack_into('<H', e, 64, min(len(enc) + 2, 64))
    struct.pack_into('BB', e, 66, etype, color)
    struct.pack_into('<III', e, 68, left, right, child)
    if clsid:
        e[80:96] = clsid
    struct.pack_into('<II', e, 116, start, size)
    return bytes(e)

ROOT_CLSID = bytes.fromhex('00000602000000000C000000000000046'[:32])
# Correct: {02060000-0000-0000-C000-000000000046}
ROOT_CLSID = b'\x00\x00\x06\x02\x00\x00\x00\x00\xC0\x00\x00\x00\x00\x00\x00\x46'
VBA_CLSID  = b'\x00\x4A\x49\x61\x00\x00\x00\x00\xC0\x00\x00\x00\x00\x00\x00\x46'

def build_vba_project(tw_src: str, m1_src: str) -> bytes:
    """Build vbaProject.bin as a valid Compound File Binary with mini-stream."""
    MINI_SZ     = 64       # mini sector size
    MINI_CUTOFF = 0x00001000  # 4096 — standard cutoff; all our streams are below it

    # ── raw stream bytes ──────────────────────────────────────────────────────
    vba_proj_data = b'\x61\x61\x4A\x00\x00\x00\xFF\xFF'
    modules = [
        {'name': 'ThisWorkbook', 'stream': 'ThisWorkbook', 'type': 0x0022, 'offset': 0},
        {'name': 'Module1',      'stream': 'Module1',      'type': 0x0021, 'offset': 0},
    ]
    dir_data    = build_dir_stream(modules)
    tw_data     = compress_vba(tw_src.encode('cp1252'))
    m1_data     = compress_vba(m1_src.encode('cp1252'))
    proj_data   = (
        'ID="{00020819-0000-0000-C000-000000000046}"\r\n'
        'Document=ThisWorkbook/&H00000000\r\n'
        'Module=Module1\r\n'
        'HelpContextID="0"\r\n'
        'VersionCompatible32="393222000"\r\n'
        'CMG=""\r\nDPB=""\r\nGC=""\r\n'
    ).encode('cp1252')
    pwm_data = b''
    for sn, mn in [('ThisWorkbook','ThisWorkbook'), ('Module1','Module1')]:
        pwm_data += sn.encode('cp1252') + b'\x00' + mn.encode('utf-16-le') + b'\x00\x00'
    pwm_data += b'\x00\x00'

    # All streams are < MINI_CUTOFF → all go in the mini-stream
    stream_order = [
        ('_VBA_PROJECT', vba_proj_data),
        ('dir',          dir_data),
        ('ThisWorkbook', tw_data),
        ('Module1',      m1_data),
        ('PROJECT',      proj_data),
        ('PROJECTwm',    pwm_data),
    ]

    # ── assign mini-sectors ───────────────────────────────────────────────────
    def ms_count(d): return max(1, -(-len(d) // MINI_SZ))

    ms_start = {}
    next_ms = 0
    for name, data in stream_order:
        ms_start[name] = next_ms
        next_ms += ms_count(data)
    total_ms = next_ms

    # ── mini-FAT (one regular sector = 128 entries, covers up to 128 mini-sectors) ──
    minifat = []
    for name, data in stream_order:
        start = ms_start[name]
        count = ms_count(data)
        for i in range(count):
            minifat.append(start + i + 1 if i < count - 1 else ENDOFCHAIN)
    while len(minifat) % 128:
        minifat.append(FREESECT)
    n_minifat_sectors = len(minifat) // 128        # typically 1

    # ── mini-stream container (lives in Root Entry's regular sector chain) ────
    mini_stream = bytearray()
    for name, data in stream_order:
        padded = data + b'\x00' * (ms_count(data) * MINI_SZ - len(data))
        mini_stream += padded
    mini_stream_size = len(mini_stream)             # = total_ms * MINI_SZ
    # pad container to regular-sector boundary
    while len(mini_stream) % SECTOR_SZ:
        mini_stream += b'\x00'
    n_container_sectors = len(mini_stream) // SECTOR_SZ

    # ── regular sector layout ─────────────────────────────────────────────────
    # 0            : FAT
    # 1–2          : directory (2 sectors → 8 entries)
    # 3..3+M-1     : MiniFAT  (M sectors, typically 1)
    # 3+M..3+M+C-1 : mini-stream container (C sectors)
    sec_fat       = 0
    sec_dir1      = 1
    sec_dir2      = 2
    sec_minifat   = 3
    sec_container = sec_minifat + n_minifat_sectors

    # ── FAT ───────────────────────────────────────────────────────────────────
    fat = [FREESECT] * 128
    fat[sec_fat]   = FATSECT
    fat[sec_dir1]  = sec_dir2
    fat[sec_dir2]  = ENDOFCHAIN
    for i in range(n_minifat_sectors):
        fat[sec_minifat + i] = (sec_minifat + i + 1
                                if i < n_minifat_sectors - 1 else ENDOFCHAIN)
    for i in range(n_container_sectors):
        fat[sec_container + i] = (sec_container + i + 1
                                  if i < n_container_sectors - 1 else ENDOFCHAIN)
    fat_sector = b''.join(struct.pack('<I', v) for v in fat)

    # ── directory entries ─────────────────────────────────────────────────────
    # Tree (right-chain siblings within same parent):
    #   Root → child=VBA
    #   VBA  → child=_VBA_PROJECT, right=PROJECT
    #   PROJECT → right=PROJECTwm
    #   _VBA_PROJECT → right=dir → right=ThisWorkbook → right=Module1
    BLACK = 0
    NO    = FREESECT

    def ms(name): return ms_start[name]
    def sz(d):    return len(d)

    entries = [
        # Root Entry: start = first container sector, size = actual mini-stream bytes
        dir_entry('Root Entry',   5, BLACK, NO, NO,  1, ROOT_CLSID,
                  sec_container, mini_stream_size),
        # VBA storage
        dir_entry('VBA',          1, BLACK, NO,  2,  4, VBA_CLSID, ENDOFCHAIN, 0),
        # Siblings of VBA at root level
        dir_entry('PROJECT',      2, BLACK, NO,  3, NO, None, ms('PROJECT'),     sz(proj_data)),
        dir_entry('PROJECTwm',    2, BLACK, NO, NO, NO, None, ms('PROJECTwm'),   sz(pwm_data)),
        # Children of VBA
        dir_entry('_VBA_PROJECT', 2, BLACK, NO,  5, NO, None, ms('_VBA_PROJECT'),sz(vba_proj_data)),
        dir_entry('dir',          2, BLACK, NO,  6, NO, None, ms('dir'),          sz(dir_data)),
        dir_entry('ThisWorkbook', 2, BLACK, NO,  7, NO, None, ms('ThisWorkbook'), sz(tw_data)),
        dir_entry('Module1',      2, BLACK, NO, NO, NO, None, ms('Module1'),      sz(m1_data)),
    ]
    dir_bytes = b''.join(entries)   # 8 × 128 = 1024 bytes

    # ── CFB header ────────────────────────────────────────────────────────────
    header = bytearray(512)
    header[0:8]   = b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'   # magic
    # bytes 8–23: CLSID (leave zero)
    header[24:26] = b'\x3E\x00'                             # minor version
    header[26:28] = b'\x03\x00'                             # major version 3
    header[28:30] = b'\xFE\xFF'                             # byte order LE
    header[30:32] = b'\x09\x00'                             # sector shift (512 = 2^9)
    header[32:34] = b'\x06\x00'                             # mini sector shift (64 = 2^6)
    struct.pack_into('<I', header, 40, 0)                   # # dir sectors (v3: 0)
    struct.pack_into('<I', header, 44, 1)                   # # FAT sectors
    struct.pack_into('<I', header, 48, sec_dir1)            # first dir sector
    struct.pack_into('<I', header, 52, 0)                   # transaction signature
    struct.pack_into('<I', header, 56, MINI_CUTOFF)         # mini stream cutoff = 4096
    struct.pack_into('<I', header, 60, sec_minifat)         # first MiniFAT sector
    struct.pack_into('<I', header, 64, n_minifat_sectors)   # # MiniFAT sectors
    struct.pack_into('<I', header, 68, ENDOFCHAIN)          # first DIFAT sector
    struct.pack_into('<I', header, 72, 0)                   # # DIFAT sectors
    struct.pack_into('<I', header, 76, sec_fat)             # DIFAT[0] = FAT sector
    for i in range(1, 109):
        struct.pack_into('<I', header, 76 + i * 4, FREESECT)

    # ── assemble ──────────────────────────────────────────────────────────────
    minifat_bytes = b''.join(struct.pack('<I', v) for v in minifat)

    cfb = bytearray(bytes(header))
    cfb += fat_sector                           # sector 0  (FAT)
    cfb += dir_bytes[:SECTOR_SZ]               # sector 1  (dir entries 0-3)
    cfb += dir_bytes[SECTOR_SZ:]               # sector 2  (dir entries 4-7)
    cfb += minifat_bytes                        # sector 3  (MiniFAT)
    cfb += bytes(mini_stream)                   # sectors 4..4+C-1 (container)

    return bytes(cfb)

# ── Workbook builder ──────────────────────────────────────────────────────────
def lane_hdr_cell(ws, row, col_start, col_end, text, bg, height=18):
    c = ws.cell(row=row, column=col_start, value=text)
    c.font = font(size=11, bold=True, color=WHITE)
    c.fill = fill(bg)
    c.alignment = align(h="left", v="center")
    ws.merge_cells(start_row=row, start_column=col_start,
                   end_row=row, end_column=col_end)
    ws.row_dimensions[row].height = height

def style_data_row(ws, row, row_bg, acc_color, num_cols):
    for c in range(1, num_cols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = fill(row_bg)
        cell.font = font()
        cell.alignment = align(wrap=(c == num_cols))
        if c == 1:
            cell.border = bdr(BORDER_CLR, left_color=acc_color, left_style="medium")
        else:
            cell.border = bdr()
    ws.row_dimensions[row].height = 16

def build_sheet_headers(ws, widths):
    headers = ["#", "Task / Initiative", "Closed Date", "Owner",
               "Due Date", "Priority", "Status", "Notes"]
    for ci, (h, w) in enumerate(zip(headers, widths), 1):
        c = ws.cell(row=1, column=ci, value=h)
        c.font = font(size=10, bold=True, color=WHITE)
        c.fill = fill(NAVY)
        c.alignment = align(h="center")
        c.border = bdr()
        ws.column_dimensions[get_column_letter(ci)].width = w
    ws.row_dimensions[1].height = 20
    ws.freeze_panes = "A2"

WIDTHS = [5, 40, 12, 16, 11, 11, 16, 38]
NCOLS  = len(WIDTHS)

def build_project_tracker(wb):
    ws = wb.create_sheet("Project Tracker")
    ws.sheet_view.showGridLines = False
    build_sheet_headers(ws, WIDTHS)

    lanes = [
        ("ACTIVE PROJECTS", ACTIVE_HDR, ACTIVE_ROW, ACTIVE_ACC, [
            [1, "Roof-deck drainage sensors — Bldg C",     "", "D. Singh",   "5/1/26",  "Medium", "In Progress", ""],
            [2, "Vendor credentialing portal rollout",      "", "K. Johnson", "4/15/26", "High",   "In Progress", "IT integration delayed 2 sprints"],
        ]),
        ("ON HOLD", HOLD_HDR, HOLD_ROW, HOLD_ACC, [
            [3, "Energy audit — Phase 2",                  "", "R. Patel",   "6/30/26", "Medium", "On Hold",     "Pending budget reallocation"],
        ]),
        ("BLOCKED", BLOCKED_HDR, BLOCKED_ROW, BLOCKED_ACC, [
            [4, "Q2 janitorial contract renewal",          "", "M. Torres",  "3/31/26", "High",   "Blocked",     "Legal redlines outstanding since 3/12/26"],
        ]),
    ]

    row = 2
    for lane_name, hdr_clr, row_clr, acc_clr, data_rows in lanes:
        lane_hdr_cell(ws, row, 1, NCOLS, f"  {lane_name}", hdr_clr)
        row += 1
        for dr in data_rows:
            for ci, val in enumerate(dr, 1):
                ws.cell(row=row, column=ci, value=val)
            ws.cell(row=row, column=5).number_format = DATE_FMT
            style_data_row(ws, row, row_clr, acc_clr, NCOLS)
            row += 1
        # spacer
        ws.row_dimensions[row].height = 6
        row += 1
    return ws

def build_open_items(wb):
    ws = wb.create_sheet("Open Items")
    ws.sheet_view.showGridLines = False
    build_sheet_headers(ws, WIDTHS)

    items = [
        [1, "Verify HVAC filter replacement compliance",      "", "R. Patel",   "3/28/26", "High",   "Overdue",   "Unit 4B overdue 2 wks — escalated"],
        [2, "Review overnight crew sign-in log",              "", "M. Torres",  "3/28/26", "Medium", "Open",      "Wed crew +22 min late — monitor"],
        [3, "Submit Q2 vendor invoice approvals to AP",       "", "K. Johnson", "4/1/26",  "Medium", "Open",      ""],
        [4, "Staff training — work-order app",                "", "J. Carter",  "4/5/26",  "Low",    "Pending",   "Vendor training deck still not delivered"],
    ]

    for ri, row_data in enumerate(items, 2):
        row_bg = SLATE_LIGHT if ri % 2 == 0 else "FFFFFF"
        for ci, val in enumerate(row_data, 1):
            c = ws.cell(row=ri, column=ci, value=val)
            c.fill = fill(row_bg)
            c.font = font()
            c.alignment = align(wrap=(ci == NCOLS))
            c.border = bdr()
        ws.cell(row=ri, column=5).number_format = DATE_FMT
        ws.row_dimensions[ri].height = 16
    return ws

def build_closed(wb):
    ws = wb.create_sheet("Closed")
    ws.sheet_view.showGridLines = False
    build_sheet_headers(ws, WIDTHS)
    # Override header color to signal archive tab
    for ci in range(1, NCOLS + 1):
        ws.cell(row=1, column=ci).fill = fill(CLOSED_HDR)
    return ws

# ── xlsm assembler ────────────────────────────────────────────────────────────
CONTENT_TYPES_TMPL = '''\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml"  ContentType="application/xml"/>
  <Default Extension="bin"  ContentType="application/vnd.ms-office.vbaProject"/>
{overrides}
</Types>'''

def make_xlsm(xlsx_path: str, vba_bin: bytes, out_path: str):
    """Inject vbaProject.bin into an xlsx zip and save as xlsm."""
    with zipfile.ZipFile(xlsx_path, 'r') as zin:
        names  = zin.namelist()
        chunks = {n: zin.read(n) for n in names}

    # 1. Content_Types.xml — swap workbook type, add bin default
    ct = chunks['[Content_Types].xml'].decode('utf-8')
    ct = ct.replace(
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml',
        'application/vnd.ms-excel.sheet.macroEnabled.main+xml'
    )
    # Build overrides from existing file, preserving all but the root Types element
    overrides = '\n'.join(
        '  ' + line.strip()
        for line in ct.splitlines()
        if line.strip().startswith('<Override') or line.strip().startswith('<Default')
    )
    # Re-parse and rebuild cleanly
    import xml.etree.ElementTree as ET
    root = ET.fromstring(ct)
    ns   = 'http://schemas.openxmlformats.org/package/2006/content-types'
    # Ensure bin default exists
    bin_ct = 'application/vnd.ms-office.vbaProject'
    has_bin = any(
        el.get('Extension') == 'bin'
        for el in root.findall(f'{{{ns}}}Default')
    )
    if not has_bin:
        el = ET.SubElement(root, f'{{{ns}}}Default')
        el.set('Extension', 'bin')
        el.set('ContentType', bin_ct)
    chunks['[Content_Types].xml'] = ET.tostring(root, xml_declaration=True,
                                                  encoding='UTF-8', short_empty_elements=True)

    # 2. xl/_rels/workbook.xml.rels — add vbaProject relationship
    rels_key = 'xl/_rels/workbook.xml.rels'
    if rels_key in chunks:
        rels = chunks[rels_key].decode('utf-8')
        if 'vbaProject' not in rels:
            vba_rel = ('  <Relationship Id="rId_vba" '
                       'Type="http://schemas.microsoft.com/office/2006/relationships/vbaProject" '
                       'Target="vbaProject.bin"/>\n')
            rels = rels.replace('</Relationships>', vba_rel + '</Relationships>')
            chunks[rels_key] = rels.encode('utf-8')

    # 3. Add vbaProject.bin
    chunks['xl/vbaProject.bin'] = vba_bin

    # 4. Write xlsm
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zout:
        for name, data in chunks.items():
            zout.writestr(name, data)

    print(f"[✓] Saved: {out_path}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    here     = os.path.dirname(os.path.abspath(__file__))
    tmp_xlsx = os.path.join(here, '_tmp_tracker.xlsx')
    out_xlsm = os.path.join(here, 'MDF_Project_Tracker.xlsm')

    # Build workbook
    wb = Workbook()
    wb.remove(wb.active)
    build_project_tracker(wb)
    build_open_items(wb)
    build_closed(wb)
    wb.save(tmp_xlsx)
    print(f"[✓] Workbook built: {tmp_xlsx}")

    # Build vbaProject.bin
    vba_bin = build_vba_project(TW_SRC, M1_SRC)
    print(f"[✓] vbaProject.bin built: {len(vba_bin)} bytes")

    # Assemble xlsm
    make_xlsm(tmp_xlsx, vba_bin, out_xlsm)

    os.remove(tmp_xlsx)

if __name__ == '__main__':
    main()
