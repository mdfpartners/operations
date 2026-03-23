#!/usr/bin/env python3
"""
Final synthesis: 561210 sub-service focus + expanded NAICS rankings.
Reads from already-fetched raw data files.
"""

import json
from collections import defaultdict

# ── Load raw data ─────────────────────────────────────────────────────────
with open("/home/user/operations/sdvosb_deepdive_raw.json") as f:
    deep = json.load(f)

with open("/home/user/operations/sdvosb_expansion_raw.json") as f:
    prev = json.load(f)

FISCAL_YEARS = [2022, 2023, 2024]

# ── PSC data from successful category query ──────────────────────────────
# (from sdvosb_deepdive_raw.json → manually replicated from stdout capture)
PSC_DISTRIBUTION = [
    ("R706", "Logistics Mgmt Support (BOS/Base Operations)",      108_010_000, 36.3),
    ("S201", "Custodial/Janitorial Services",                       64_310_000, 21.7),
    ("J025", "Vehicle Equipment Maint/Repair",                      17_380_000,  5.9),
    ("S216", "Facilities Operations Support",                       14_500_000,  4.9),
    ("Z1AZ", "Real Property Maintenance — Other",                   12_290_000,  4.1),
    ("R499", "Professional Support — Other",                         9_800_000,  3.3),
    ("Z1AA", "Real Property Maintenance — Office Bldgs",             9_590_000,  3.2),
    ("J059", "HVAC Equipment Maintenance",                           6_340_000,  2.1),
    ("J041", "Refrigeration Equipment Maint/Repair",                 5_770_000,  2.0),
    ("C1QA", "Architect/Engineering — Construction",                 5_600_000,  1.9),
    ("J045", "Plumbing/Heating Equipment Maint",                     4_890_000,  1.7),
    ("R430", "Physical Security Services (Professional)",            4_430_000,  1.5),
    ("R408", "Program Management/Support",                           4_100_000,  1.4),
    ("J065", "Medical Equipment Maintenance",                        4_060_000,  1.4),
    ("Z1DA", "Hospital/Infirmary Maintenance",                       3_310_000,  1.1),
    ("F103", "Environmental — Water Quality Protection",             3_050_000,  1.0),
    ("Other","Other/Uncategorized PSC Codes",                       13_570_000,  4.6),
]

TOTAL_561210_3YR = 297_000_000  # from category query (approx from psc totals)

# ── Award description sample (from deep dive stdout) ──────────────────────
DESC_COUNTS = {
    "General Maintenance":              11,
    "Custodial/Janitorial":              7,
    "Operations & Maintenance (O&M)":    5,
    "General Support Services":          4,
    "Logistics Support":                 4,
    "Base Operations Support (BOS)":     2,
    "Energy Management":                 1,
    "Grounds Maintenance":               1,
    "Uncategorized/Other":              15,
}

# ── New NAICS data ───────────────────────────────────────────────────────
NEW_DATA = deep["new_naics_data"]

NEW_LABELS = {
    "238220": "Plumbing/HVAC Contractors",
    "238210": "Electrical Contractors",
    "238990": "Other Specialty Trade Contractors",
    "236220": "Commercial/Institutional Building Construction",
    "811310": "Commercial Machinery/Equip Repair & Maint",
    "562910": "Remediation Services",
    "561990": "All Other Support Services",
    "237310": "Highway, Street & Bridge Construction",
    "541513": "Computer Facilities Mgmt Services",
    "561621": "Security Systems Services",
}

# Previous top-5 data for comparison
PREV_TOP5 = {
    "561210": "Facilities Support Services",
    "561720": "Janitorial Services",
    "493110": "General Warehousing & Storage",
    "561612": "Security Guards & Patrol",
    "561320": "Temporary Staffing",
}

WEIGHTS = {
    "market_size_growth": 0.30,
    "avg_contract_value": 0.25,
    "competitor_count":   0.25,
    "accessibility":      0.20,
}


def fmt_dollars(n):
    if not n:
        return "$0"
    if n >= 1_000_000_000:
        return f"${n/1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"${n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"${n/1_000:.0f}K"
    return f"${n:.0f}"


def fmt_pct(n):
    if n is None:
        return "—"
    sign = "+" if n >= 0 else ""
    return f"{sign}{n:.0f}%"


def fmt_num(n):
    if n is None:
        return "—"
    if isinstance(n, str):
        return n
    return f"{int(n):,}"


def normalize(values, invert=False):
    nums = [v for v in values if isinstance(v, (int, float))]
    if not nums or max(nums) == min(nums):
        return {i: 0.5 for i in range(len(values))}
    lo, hi = min(nums), max(nums)
    result = {}
    for i, v in enumerate(values):
        if not isinstance(v, (int, float)):
            result[i] = 0.0
        else:
            norm = (v - lo) / (hi - lo)
            result[i] = (1 - norm) if invert else norm
    return result


def compute_scores(all_data):
    codes = list(all_data.keys())
    totals, avgs, competitors, accessibilities, growths = [], [], [], [], []

    for code in codes:
        d = all_data[code]
        yearly = d["yearly"]
        total_obs = sum(v["obligations"] for v in yearly.values())
        total_cnt = sum(v["contracts"] for v in yearly.values())
        avg_val = total_obs / total_cnt if total_cnt > 0 else 0
        fy22 = yearly.get(2022, {}).get("obligations", 0) or yearly.get("2022", {}).get("obligations", 0)
        fy24 = yearly.get(2024, {}).get("obligations", 0) or yearly.get("2024", {}).get("obligations", 0)
        growth = ((fy24 - fy22) / fy22 * 100) if fy22 > 0 else 0
        # Cap growth influence — explosive growth codes that are tiny shouldn't dominate
        growth_cap = min(growth, 200)
        market_raw = total_obs * (1 + max(growth_cap, -50) / 100)

        comp = d.get("unique_awardees", 999)
        comp_num = int(str(comp).replace("+", "")) if isinstance(comp, str) else (comp or 999)
        # Treat 200+ as 250 for scoring
        if isinstance(d.get("unique_awardees"), str) and "+" in str(d.get("unique_awardees")):
            comp_num = 250

        num_agencies = len(d.get("top_agencies", []))
        access_raw = 0
        if 0 < avg_val <= 2_000_000:
            access_raw += 40
        if 0 < avg_val <= 750_000:
            access_raw += 20
        if num_agencies >= 3:
            access_raw += 20
        if growth > -10:
            access_raw += 20

        totals.append(market_raw)
        avgs.append(avg_val)
        competitors.append(comp_num)
        accessibilities.append(access_raw)
        growths.append(growth)

    n_market = normalize(totals)
    n_avg = normalize(avgs)
    n_comp = normalize(competitors, invert=True)
    n_access = normalize(accessibilities)

    scores = {}
    details = {}
    for i, code in enumerate(codes):
        s = (WEIGHTS["market_size_growth"] * n_market[i] +
             WEIGHTS["avg_contract_value"] * n_avg[i] +
             WEIGHTS["competitor_count"]   * n_comp[i] +
             WEIGHTS["accessibility"]      * n_access[i])
        scores[code] = round(s * 100, 1)
        yearly = all_data[code]["yearly"]
        total_obs = sum(v["obligations"] for v in yearly.values())
        total_cnt = sum(v["contracts"] for v in yearly.values())
        details[code] = {
            "total_obs": total_obs,
            "total_cnt": total_cnt,
            "avg_val": total_obs / total_cnt if total_cnt else 0,
            "growth": growths[i],
            "market_n": round(n_market[i]*100, 1),
            "avg_n":    round(n_avg[i]*100, 1),
            "comp_n":   round(n_comp[i]*100, 1),
            "access_n": round(n_access[i]*100, 1),
        }
    return scores, details


def run():
    W = 72

    # ═══════════════════════════════════════════════════════════════════════
    # REPORT 1 — 561210 Internal Sub-Service Map
    # ═══════════════════════════════════════════════════════════════════════
    print("=" * W)
    print("  REPORT 1: WHAT'S INSIDE NAICS 561210")
    print("  Product/Service Code Distribution — FY2022–2024, SDVOSB Only")
    print("=" * W)

    print(f"\n  {'PSC':<6} {'Service Line':<42} {'3Y Obligated':>13}  {'Share':>6}")
    print("  " + "─" * 71)
    for code, label, amt, pct in PSC_DISTRIBUTION:
        bar = "█" * int(pct / 2)
        print(f"  {code:<6} {label:<42} {fmt_dollars(amt):>13}  {pct:>5.1f}%  {bar}")

    print(f"\n  Note: Amounts are within-561210 distributions derived from")
    print(f"  the PSC category endpoint. Total 3-year 561210 SDVOSB ≈ $297M.")

    print(f"""
  WHAT THE PSC MAP REVEALS:

  ┌─────────────────────────────────────────────────────────────────┐
  │ TIER 1 — The Core of 561210 (58% of volume)                    │
  │                                                                  │
  │  R706  Base Operations Support / Logistics Mgmt  36% / $108M   │
  │  S201  Custodial & Janitorial                    22% / $64M    │
  │                                                                  │
  │ TIER 2 — Secondary but Meaningful (17% combined)               │
  │                                                                  │
  │  J025  Vehicle/Equipment Maintenance              6% / $17M    │
  │  S216  Facilities Operations Support              5% / $14M    │
  │  Z1AZ  Real Property Maintenance                  4% / $12M    │
  │  Z1AA  Office Building Maintenance                3% / $10M    │
  │                                                                  │
  │ TIER 3 — Specialty Trades (7% combined)                        │
  │                                                                  │
  │  J059  HVAC Equipment Maintenance                 2% / $6M     │
  │  J041  Refrigeration Equipment Maint              2% / $6M     │
  │  J045  Plumbing/Heating Equipment Maint           2% / $5M     │
  └─────────────────────────────────────────────────────────────────┘

  The top-50 award description analysis reinforces this:
  "General Maintenance" (22%), "Custodial" (14%), and "O&M" (10%)
  are the dominant contract types visible in award titles.
  "Base Operations Support (BOS)" appears in the largest single
  awards ($67M–$152M range) — these are bundled multi-service contracts.
""")

    print("  FOCUS RECOMMENDATION WITHIN 561210:")
    print()
    print("  ► For a firm with janitorial past performance:")
    print("    S201 (Custodial) + S216 (Facilities Ops Support)")
    print("    This is the direct extension — same labor model, same site type,")
    print("    just a wider scope of building services tasks. Register under 561210")
    print("    and explicitly reference S201/S216 in your capability statement.")
    print()
    print("  ► Medium-term (12–24 months):")
    print("    Z1AZ/Z1AA (Real Property Maintenance)")
    print("    Add preventive maintenance, inspections, and minor repair scope.")
    print("    Subcontract the trade work (HVAC, plumbing) initially; prime later.")
    print()
    print("  ► DO NOT target R706 (BOS) as a first prime:")
    print("    BOS contracts run $50M–$150M+, require bonded logistics capability,")
    print("    and compete against firms with 10–20 year incumbent records at")
    print("    specific military installations. These are Year 3–5 targets at best.")

    # ═══════════════════════════════════════════════════════════════════════
    # REPORT 2 — New NAICS Raw Summary
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * W)
    print("  REPORT 2: NEW NAICS CODES — FULL DATA SUMMARY")
    print("  FY2022–2024 | SDVOSB Set-Aside Only")
    print("=" * W)

    print(f"\n  {'NAICS':<8} {'Description':<36} {'3Y Total':>10}  {'Awards':>7}  {'Avg Val':>10}  {'YoY%':>7}  {'Awardees':>9}")
    print("  " + "─" * 92)
    for code, label in NEW_LABELS.items():
        d = NEW_DATA.get(code, {})
        yearly_raw = d.get("yearly", {})
        # Handle both int and string keys
        yearly = {}
        for fy in FISCAL_YEARS:
            yearly[fy] = (yearly_raw.get(fy) or yearly_raw.get(str(fy)) or {})
        total_obs = sum(v.get("obligations", 0) for v in yearly.values())
        total_cnt = sum(v.get("contracts", 0) for v in yearly.values())
        avg_val = total_obs / total_cnt if total_cnt else 0
        fy22 = yearly.get(2022, {}).get("obligations", 0)
        fy24 = yearly.get(2024, {}).get("obligations", 0)
        growth = ((fy24 - fy22) / fy22 * 100) if fy22 > 0 else 0
        uniq = d.get("unique_awardees", "—")
        print(f"  {code:<8} {label[:35]:<36} {fmt_dollars(total_obs):>10}  {fmt_num(total_cnt):>7}  "
              f"{fmt_dollars(avg_val):>10}  {fmt_pct(growth):>7}  {fmt_num(uniq):>9}")

    # ═══════════════════════════════════════════════════════════════════════
    # REPORT 3 — Combined Scoring (Previous + New, excluding 236220)
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * W)
    print("  REPORT 3: COMBINED RANKING — PREV TOP 5 + NEW NAICS")
    print(f"  Weights: Market/Growth {WEIGHTS['market_size_growth']*100:.0f}%  "
          f"Avg Value {WEIGHTS['avg_contract_value']*100:.0f}%  "
          f"Competition {WEIGHTS['competitor_count']*100:.0f}%  "
          f"Accessibility {WEIGHTS['accessibility']*100:.0f}%")
    print("=" * W)

    # Build combined dataset
    combined = {}
    for code, label in PREV_TOP5.items():
        if code in prev:
            entry = dict(prev[code])
            entry["label"] = label
            # Fix key types for yearly
            raw_yearly = entry.get("yearly", {})
            fixed = {}
            for fy in FISCAL_YEARS:
                v = raw_yearly.get(fy) or raw_yearly.get(str(fy)) or {}
                fixed[fy] = v
            entry["yearly"] = fixed
            combined[code] = entry

    # Add new NAICS (excluding 236220 — it's construction, different risk profile)
    EXCLUDE = {"236220"}  # construction bonding/licensure barrier makes it non-comparable
    for code, d in NEW_DATA.items():
        if code in EXCLUDE:
            continue
        entry = dict(d)
        entry["label"] = NEW_LABELS.get(code, code)
        raw_yearly = entry.get("yearly", {})
        fixed = {}
        for fy in FISCAL_YEARS:
            v = raw_yearly.get(fy) or raw_yearly.get(str(fy)) or {}
            fixed[fy] = v
        entry["yearly"] = fixed
        combined[code] = entry

    scores, details = compute_scores(combined)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    print(f"\n  {'Rk':<4} {'NAICS':<8} {'Description':<32}  {'3Y Total':>10}  {'Awards':>6}  "
          f"{'Avg':>9}  {'YoY%':>6}  {'Score':>6}  {'Tag'}")
    print("  " + "─" * 98)
    for i, (code, score) in enumerate(ranked, 1):
        det = details[code]
        label = combined[code]["label"][:31]
        tag = "NEW" if code in NEW_LABELS else "prev"
        print(f"  {i:<4} {code:<8} {label:<32}  {fmt_dollars(det['total_obs']):>10}  "
              f"{fmt_num(det['total_cnt']):>6}  {fmt_dollars(det['avg_val']):>9}  "
              f"{fmt_pct(det['growth']):>6}  {score:>6.1f}  {tag}")

    # Dimension breakdown for top 8
    print(f"\n  Scoring dimension detail (top 8):")
    print(f"  {'NAICS':<8} {'Description':<30}  {'Mkt(30)':>7}  {'Val(25)':>7}  {'Comp(25)':>8}  {'Acc(20)':>7}  {'TOTAL':>6}")
    print("  " + "─" * 82)
    for code, score in ranked[:8]:
        det = details[code]
        label = combined[code]["label"][:29]
        print(f"  {code:<8} {label:<30}  {det['market_n']:>7.1f}  {det['avg_n']:>7.1f}  "
              f"{det['comp_n']:>8.1f}  {det['access_n']:>7.1f}  {score:>6.1f}")

    # ═══════════════════════════════════════════════════════════════════════
    # FINAL SYNTHESIS
    # ═══════════════════════════════════════════════════════════════════════
    top5 = ranked[:5]

    print("\n" + "=" * W)
    print("  FINAL SYNTHESIS & STRATEGIC RECOMMENDATIONS")
    print("=" * W)

    print(f"""
┌──────────────────────────────────────────────────────────────────────┐
│  PART A: WHAT TO FOCUS ON WITHIN 561210                             │
└──────────────────────────────────────────────────────────────────────┘

  Register under NAICS 561210, but pitch TWO specific PSC sub-services:

  PRIMARY FOCUS — S201 + S216 (Custodial → Facilities Ops)
  ─────────────────────────────────────────────────────────
  Combined these represent 27% ($79M) of all 561210 SDVOSB spend.
  S201 is direct janitorial work — identical to your current 561720
  past performance, just under the broader NAICS umbrella. S216 adds
  facilities operations coordination: managing vendor schedules,
  work orders, preventive maintenance logs, and site compliance.
  Any firm already cleaning federal buildings can credibly pitch this.

  SECONDARY FOCUS — Z1AZ / Z1AA (Real Property Maintenance)
  ──────────────────────────────────────────────────────────
  Combined 7% ($22M) of 561210 SDVOSB spend, and these codes appear
  on recompetes that are often below the $2M simplified acquisition
  threshold — small, direct-award-eligible work. The tasks are
  routine: inspections, minor repairs, upkeep. Subcontract the
  licensed trade work (HVAC, plumbing) until you build in-house
  capacity; you can prime from day one.

  AVOID (until Year 3+) — R706 (Base Operations Support / BOS)
  ─────────────────────────────────────────────────────────────
  BOS is 36% of 561210 volume but the individual contract sizes run
  $50M–$150M. These are multi-year, bundled contracts at military
  installations requiring incumbency records, bonded logistics subs,
  and often an existing customer relationship. This is not a 12-18
  month target for a new entrant — it's the aspirational contract
  after you've accumulated two or three relevant task order records.

┌──────────────────────────────────────────────────────────────────────┐
│  PART B: NEW NAICS THAT DESERVE SERIOUS CONSIDERATION               │
└──────────────────────────────────────────────────────────────────────┘
""")

    # Pull key new entrants from ranking
    new_in_top8 = [(c, s) for c, s in ranked[:8] if c in NEW_LABELS and c not in EXCLUDE]
    for code, score in new_in_top8[:3]:
        d = combined[code]
        det = details[code]
        print(f"  ★ {code} — {d['label']}")
        print(f"    Score: {score:.1f}/100 | {fmt_dollars(det['total_obs'])} / 3 yrs | "
              f"Avg: {fmt_dollars(det['avg_val'])} | YoY: {fmt_pct(det['growth'])} | "
              f"Awardees: {fmt_num(d.get('unique_awardees'))}")
        for ag in d.get("top_agencies", [])[:2]:
            print(f"    Buyer: {ag['name']}: {fmt_dollars(ag['amount'])}")
        print()

    # Specific commentary
    print("""  238220 — Plumbing, Heating, HVAC Contractors
  ──────────────────────────────────────────────
  The biggest surprise in the expanded analysis. $426M over 3 years,
  1,333 awards, $320K average, and +50% YoY growth. That is the
  single best growth story in the entire 27-NAICS universe we analyzed.
  The catch: 200+ unique SDVOSB awardees make it competitive. But
  the market is so large and so fragmented — 1,333 awards means
  roughly 444 new contracts per year, spread across DoD, VA, and
  civilian agencies — that a focused entrant can carve meaningful
  share. If the firm can hire or partner with licensed HVAC/plumbing
  tradespeople, this code deserves to sit alongside 561210 in the
  short-term pipeline. You don't need a license to prime; you need
  a licensed subcontractor on your team.

  561990 — All Other Support Services
  ────────────────────────────────────
  $126M, +64% growth, only 61 awardees. This is the "catch-all" code
  contracting officers use for bundled support services that don't fit
  neatly elsewhere. Average contract is $250K — squarely in simplified
  acquisition territory. With 61 awardees vs 162 in 561210, competition
  is lighter. Add this as a secondary NAICS registration today; it
  costs nothing and opens bid eligibility on contracts that would
  otherwise pass you by.

  541513 — Computer Facilities Management Services
  ─────────────────────────────────────────────────
  $154M over 3 years, avg $2.5M per contract, only 25 awardees.
  The extremely low competition is attractive, but the $2.5M average
  signals these are sophisticated IT infrastructure contracts (data
  center O&M, server room management, enterprise HVAC for tech).
  This is a Year 2–3 target if the firm can establish a credible
  technology partnership; do not attempt to prime without it.

  236220 — Commercial/Institutional Building Construction
  ────────────────────────────────────────────────────────
  $6.38B is the largest number in the analysis — but this is VA
  construction (VA holds $6.1B of the $6.38B). These are construction
  contracts requiring GC licenses, bonding capacity, and construction
  past performance. Not the right fit for a facilities services firm
  unless you pivot to a full construction capability. Flagged here
  for completeness; remove from consideration for now.""")

    print(f"""
┌──────────────────────────────────────────────────────────────────────┐
│  FINAL RECOMMENDED REGISTRATION STACK                               │
└──────────────────────────────────────────────────────────────────────┘

  Add these NAICS codes to SAM.gov + SDVOSB certification today:

  PRIMARY (pursue immediately):
  ┌────────┬──────────────────────────────────────┬────────────────────┐
  │ NAICS  │ Service Line                         │ Rationale          │
  ├────────┼──────────────────────────────────────┼────────────────────┤
  │ 561210 │ Facilities Support Services          │ #1 expansion NAICS │
  │        │ Focus: S201 + S216 PSC sub-types     │ direct adjacency   │
  ├────────┼──────────────────────────────────────┼────────────────────┤
  │ 238220 │ Plumbing/HVAC Contractors            │ $426M, +50% growth │
  │        │ Partner with licensed tradespeople   │ most active market │
  └────────┴──────────────────────────────────────┴────────────────────┘

  SECONDARY (register now, pursue in parallel):
  ┌────────┬──────────────────────────────────────┬────────────────────┐
  │ NAICS  │ Service Line                         │ Rationale          │
  ├────────┼──────────────────────────────────────┼────────────────────┤
  │ 561990 │ All Other Support Services           │ 61 awardees, +64%  │
  │ 238990 │ Other Specialty Trade Contractors    │ natural bridge code │
  └────────┴──────────────────────────────────────┴────────────────────┘

  HOLD (year 2–3):
  ┌────────┬──────────────────────────────────────┬────────────────────┐
  │ NAICS  │ Service Line                         │ Rationale          │
  ├────────┼──────────────────────────────────────┼────────────────────┤
  │ 541513 │ Computer Facilities Mgmt Services    │ needs tech partner │
  │ 561210 │ R706 BOS contracts                   │ $50M+ incumbents   │
  └────────┴──────────────────────────────────────┴────────────────────┘

  FIRST 60 DAYS:
    1. Add 561210, 238220, 561990, 238990 to SAM.gov NAICS list
    2. Pull all SDVOSB set-aside solicitations in those codes
       expiring in the next 12 months at VA + DoD
    3. Identify 2–3 solicitations under S201/S216 PSC codes at the VA
       (VA held $129M of 561210 and $202M of 561720 — your strongest
       reference agency)
    4. Build one capability statement per target NAICS; reference
       specific PSC codes in the "Core Competencies" section
    5. For 238220: identify a licensed HVAC/plumbing subcontractor in
       your geography — you need them named in proposals
""")

    print("=" * W)
    print("[Data: USASpending.gov API v2 | FY2022–2024 | Retrieved March 2026]")
    print("[Set-aside: SDVOSBC (competitive) + SDVOSBS (sole source)]")
    print("[236220 excluded from scoring: construction bonding/licensure barrier]")
    print("=" * W)


if __name__ == "__main__":
    run()
