#!/usr/bin/env python3
"""
Final synthesis v3: Full 31-NAICS universe including consulting codes.
Addresses: (1) why staffing underperformed, (2) consulting opportunity.
"""

import json

with open("/home/user/operations/full_universe_scores.json") as f:
    universe = json.load(f)
with open("/home/user/operations/consulting_naics_raw.json") as f:
    consult = json.load(f)

scores = universe["scores"]
metrics = universe["metrics"]

W = 72


def fmt(n):
    if not n:
        return "$0"
    n = float(n)
    if n >= 1e9:
        return f"${n/1e9:.2f}B"
    if n >= 1e6:
        return f"${n/1e6:.1f}M"
    if n >= 1e3:
        return f"${n/1e3:.0f}K"
    return f"${n:.0f}"


def fmtpct(n):
    n = float(n)
    return f"{n:+.0f}%"


ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)


def run():

    # ═══════════════════════════════════════════════════════════════════════
    # REPORT 1 — Why Staffing Underperformed
    # ═══════════════════════════════════════════════════════════════════════
    print("=" * W)
    print("  REPORT 1: WHY STAFFING CODES SCORE POORLY")
    print("  561612 Security Guards | 561320 Temp Staffing")
    print("=" * W)

    staffing = {
        "561612": {"label": "Security Guards & Patrol",
                   "detail": "The SDVOSB set-aside channel for guard services fell -20% from "
                             "FY22 to FY24. This mirrors a federal-wide shift: agencies are "
                             "consolidating security contracts onto large IDIQ vehicles (GSA "
                             "MAS Security, DHS EAGLE II) that reduce direct set-aside awards. "
                             "Guard-to-technology substitution (access control, cameras) is also "
                             "reducing officer headcount requirements on smaller sites. The 46 "
                             "unique awardees mean competition is manageable IF you're already "
                             "an incumbent — but for a new entrant the declining volume makes "
                             "this a shrinking pie."},
        "561320": {"label": "Temporary Staffing",
                   "detail": "The -46% collapse is the worst trend in the entire 31-NAICS "
                             "universe. SDVOSB set-aside spending on temp staffing has been "
                             "cut nearly in half over three years. This reflects a deliberate "
                             "shift in federal HR strategy — agencies are moving to direct "
                             "hire, PEO models (561330), and IDIQ vehicles that consolidate "
                             "staffing under a single prime. The 812 awards show there are "
                             "still contracts, but total dollars dropped from ~$170M in FY22 "
                             "to ~$92M in FY24. This is not a market to build a growth "
                             "strategy around."},
    }

    for code, d in staffing.items():
        m = metrics.get(code, {})
        print(f"\n  {code} — {d['label']}")
        print(f"  3Y Total: {fmt(m.get('total_obs',0))} | Awards: {m.get('total_cnt','?')} | "
              f"Avg: {fmt(m.get('avg_val',0))} | Growth: {fmtpct(m.get('growth',0))} | "
              f"Awardees: {m.get('awardees','?')} | Score: {scores.get(code,'?')}/100")
        print()
        # Word-wrap at 68 chars
        words = d["detail"].split()
        line = "  "
        for w in words:
            if len(line) + len(w) + 1 > 70:
                print(line)
                line = "  " + w
            else:
                line += (" " if len(line) > 2 else "") + w
        print(line)

    print(f"""
  BOTTOM LINE ON STAFFING:
  Both 561612 and 561320 score in the bottom half of the expanded
  universe specifically because of declining SDVOSB spend trends —
  not because the firms are bad businesses, but because the federal
  set-aside channel for these services is actively contracting.
  If your core is security staffing, the revenue path in the federal
  market is not through SDVOSB set-asides; it's through GSA Schedule
  MAS or direct agency BPAs where volume is larger and more stable.
  For SDVOSB set-aside certification to create maximum value, it
  should be targeted at growing sub-markets, not declining ones.
""")

    # ═══════════════════════════════════════════════════════════════════════
    # REPORT 2 — Consulting NAICS Full Data
    # ═══════════════════════════════════════════════════════════════════════
    print("=" * W)
    print("  REPORT 2: CONSULTING NAICS CODES — FULL DATA")
    print("  FY2022–2024 | SDVOSB Set-Aside Only")
    print("=" * W)

    consult_codes = ["541611", "541614", "541618", "541690", "541620",
                     "541990", "541330"]
    print(f"\n  {'NAICS':<8} {'Description':<32} {'3Y Total':>10}  {'Awards':>6}  "
          f"{'Avg Val':>9}  {'YoY%':>7}  {'Awardees':>9}")
    print("  " + "─" * 88)
    for code in consult_codes:
        m = metrics.get(code)
        if not m:
            continue
        print(f"  {code:<8} {m['label'][:31]:<32} {fmt(m['total_obs']):>10}  "
              f"{str(m.get('total_cnt','?')):>6}  {fmt(m['avg_val']):>9}  "
              f"{fmtpct(m['growth']):>7}  {str(m['awardees']):>9}")

    # Top agency buyers for key consulting codes
    print(f"\n  Top agency buyers:")
    for code in ["541611", "541614", "541618"]:
        cd = consult.get(code, {})
        print(f"\n  {code} — {cd.get('label', code)}")
        for ag_name, ag_amt in cd.get("agencies", [])[:3]:
            print(f"    {ag_name[:58]:<58}  {fmt(ag_amt)}")

    print(f"""
  KEY CONSULTING OBSERVATIONS:

  541611 (Admin Mgmt Consulting) — $1.53B, +45% growth
  ──────────────────────────────────────────────────────
  The VA alone spent $966M on administrative management consulting
  under the SDVOSB set-aside. This is the single largest SDVOSB market
  we have identified — larger than 561210, 561320, or any facilities
  code. The contracts cover operational process improvement, healthcare
  administration, organizational management, and program support.
  The $1.5M average contract value is higher than most facilities codes,
  but the 100+ awardees means the market is accessible if you can
  demonstrate relevant past performance.

  541614 (Process/Logistics Consulting) — $114M, $1.2M avg, 36 awardees
  ───────────────────────────────────────────────────────────────────────
  This is the most strategically interesting consulting code for a
  firm with facilities/operations background. "Process consulting"
  in the federal context means operational efficiency analysis,
  supply chain review, logistics workflow improvement — exactly the
  type of analytical work that a firm running Base Operations Support
  (BOS) contracts builds naturally. With only 36 awardees and $1.2M
  average contracts, this is a high-value, lower-competition niche.
  DoD and VA split the market roughly evenly.

  541618 (Other Mgmt Consulting) — $17.4M, +83% growth, 12 awardees
  ───────────────────────────────────────────────────────────────────
  Small absolute market but the highest growth rate in the consulting
  group (+83%) and only 12 awardees. Worth watching as a secondary
  registration — low effort, could capture niche advisory work.

  541330 (Engineering Services) — $1.53B, +46% growth
  ──────────────────────────────────────────────────────
  Equal in size to 541611 and growing fast, but this requires
  professional engineering (PE) credentials. Not accessible without
  a licensed engineer as a principal or key personnel. Flag for
  a future teaming/subcontracting strategy — find a PE firm to
  partner with and potentially prime under 541330 later.
""")

    # ═══════════════════════════════════════════════════════════════════════
    # REPORT 3 — Full Universe Top-15 Ranking
    # ═══════════════════════════════════════════════════════════════════════
    print("=" * W)
    print("  REPORT 3: FULL 31-NAICS UNIVERSE — TOP 15 RANKING")
    print(f"  Weights: Mkt/Growth 30% | Avg Value 25% | Competition 25% | Access 20%")
    print("=" * W)

    print(f"\n  {'Rk':<4} {'NAICS':<8} {'Description':<32}  {'3Y Total':>10}  {'Avg':>9}  "
          f"{'YoY%':>7}  {'Awardees':>9}  {'Score':>6}  {'Type'}")
    print("  " + "─" * 102)
    type_tags = {"prev": "facility", "new": "trades", "consult": "CONSULTING"}
    for i, (code, score) in enumerate(ranked[:15], 1):
        m = metrics[code]
        tag = type_tags.get(m.get("src", ""), "")
        print(f"  {i:<4} {code:<8} {m['label'][:31]:<32}  {fmt(m['total_obs']):>10}  "
              f"{fmt(m['avg_val']):>9}  {fmtpct(m['growth']):>7}  {str(m['awardees']):>9}  "
              f"{score:>6.1f}  {tag}")

    # ═══════════════════════════════════════════════════════════════════════
    # FINAL SYNTHESIS
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * W)
    print("  FINAL SYNTHESIS: REVISED STRATEGIC PICTURE")
    print("=" * W)

    print(f"""
The addition of consulting NAICS codes materially changes the picture.
Here is the corrected strategic landscape:

┌──────────────────────────────────────────────────────────────────────┐
│  TIER 1: REGISTER IMMEDIATELY                                       │
│  These codes have active, accessible SDVOSB markets and align       │
│  with an operations-capable firm's credible scope                   │
└──────────────────────────────────────────────────────────────────────┘

  561210  Facilities Support Services         Score: 36.7
  ─────────────────────────────────────────────────────
  Still the primary facilities code. Register under it, pitch S201
  (custodial) and S216 (facilities ops) PSC sub-types specifically.
  Do not bid it generically as "facilities support."

  561990  All Other Support Services          Score: 44.0
  ─────────────────────────────────────────────────────
  $126M, +64% growth, only 61 awardees. Register now, costs nothing.
  Captures bundled service contracts that straddle NAICS lines.

  541614  Process/Logistics Consulting        Score: 48.7
  ─────────────────────────────────────────────────────
  $114M, 36 awardees, $1.2M avg. The single best consulting code for
  a firm that runs facilities/BOS operations — the analytical work
  (process mapping, workflow optimization, logistics assessment) is
  exactly what operators learn from running multi-service contracts.
  If you have any operational analysis or advisory work in your past
  performance, register this immediately and start pitching it.

┌──────────────────────────────────────────────────────────────────────┐
│  TIER 2: REGISTER NOW, BUILD CAPABILITY IN 6-12 MONTHS             │
└──────────────────────────────────────────────────────────────────────┘

  541611  Admin Mgmt Consulting               Score: 58.1  ← #1 overall
  ─────────────────────────────────────────────────────
  $1.53B over 3 years, +45% growth, VA dominates at $966M. This is
  the largest SDVOSB market in the entire analysis. The barrier is
  past performance — you need at least one consulting engagement on
  your record before you can credibly compete. The path in: start
  as a subcontractor on a 541611 award; capture a prime opportunity
  after your first year. The upside is enormous.

  238220  Plumbing/HVAC Contractors           Score: 31.4
  ─────────────────────────────────────────────────────
  $426M, +50% growth, 1,333 contracts/year. Despite scoring lower
  in the full universe (market normalization effect from the
  consulting giants), this is still the highest-volume active
  contract opportunity in the trades/facilities space. 200+ awardees
  but 444 new contracts annually means there is room for a focused
  entrant. Partner with a licensed HVAC sub.

┌──────────────────────────────────────────────────────────────────────┐
│  TIER 3: WATCH, TEAM ON, DON'T PRIME YET                           │
└──────────────────────────────────────────────────────────────────────┘

  541330  Engineering Services               Score: 57.1  ← #2 overall
  ─────────────────────────────────────────────────────
  $1.53B and +46% growth makes this the co-largest market with 541611.
  Cannot prime without PE credentials. Find an engineering firm to
  team with — you bring the operations capability and past performance
  on multi-service contracts; they bring the license. The VA construction
  and facilities engineering pipeline is enormous.

  541513  Computer Facilities Mgmt           Score: 49.8
  ─────────────────────────────────────────────────────
  25 awardees, $154M, $2.5M avg. Still a high-value niche.
  Needs a technology/data center operations partner to pursue.

┌──────────────────────────────────────────────────────────────────────┐
│  DO NOT PURSUE — SDVOSB SET-ASIDE CHANNEL IS DECLINING             │
└──────────────────────────────────────────────────────────────────────┘

  561320  Temporary Staffing                 -46% YoY — collapsing
  ─────────────────────────────────────────────────────
  If staffing is a core business, the federal revenue path is GSA MAS
  (Schedule 736 / Temp Staffing SIN) and agency BPAs — not SDVOSB
  set-asides. Set-aside dollars here have been cut in half in 3 years.

  561612  Security Guards & Patrol           -20% YoY — declining
  ─────────────────────────────────────────────────────
  $257M is still a real market, but the trend is moving against you.
  Score drops from 50.6 (when evaluated in isolation) to 43.5 in the
  full universe. If you have existing guard contracts, protect them,
  but do not build a growth pipeline around new set-aside guard work.
  The better pivot is 541611 (admin/ops consulting) or 561210 (broader
  facilities) where your security operations experience becomes a
  differentiator in capability statements.

┌──────────────────────────────────────────────────────────────────────┐
│  REVISED NAICS REGISTRATION STACK                                   │
└──────────────────────────────────────────────────────────────────────┘

  Add to SAM.gov + SDVOSB cert today:
  ┌────────┬──────────────────────────────────────┬────────────────────┐
  │ NAICS  │ Service Line                         │ Priority           │
  ├────────┼──────────────────────────────────────┼────────────────────┤
  │ 561210 │ Facilities Support (S201/S216 focus) │ Primary — now      │
  │ 541614 │ Process/Logistics Consulting         │ Primary — now      │
  │ 561990 │ All Other Support Services           │ Primary — now      │
  ├────────┼──────────────────────────────────────┼────────────────────┤
  │ 541611 │ Admin Mgmt Consulting                │ Secondary — now    │
  │ 238220 │ Plumbing/HVAC (with licensed sub)    │ Secondary — now    │
  │ 238990 │ Other Specialty Trades               │ Secondary — now    │
  ├────────┼──────────────────────────────────────┼────────────────────┤
  │ 541330 │ Engineering (needs PE partner)        │ Hold — team first  │
  │ 541513 │ Computer Facilities (needs IT partner)│ Hold — team first  │
  └────────┴──────────────────────────────────────┴────────────────────┘

  KEY STRATEGIC SHIFT:
  The consulting codes (541611, 541614) open a fundamentally different
  revenue ceiling than facilities/staffing codes. A $250K janitorial
  award and a $1.5M process consulting award require similar BD effort
  but produce very different growth trajectories. The operational
  credibility built from running facilities and security contracts is
  exactly the past performance that makes 541614 (logistics/process
  consulting) bids credible. The pivot from "we clean your building"
  to "we optimize your facility operations" is a capability statement
  reframe, not a new business.
""")

    print("=" * W)
    print("[Data: USASpending.gov API v2 | FY2022–2024 | Retrieved March 2026]")
    print("[31 NAICS codes across facilities, staffing, trades, consulting]")
    print("[Excluded: 236220 construction, 541715 R&D, 541519 pure IT, inactive codes]")
    print("=" * W)


if __name__ == "__main__":
    run()
