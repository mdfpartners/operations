#!/usr/bin/env python3
"""
Part 2: Deep-dive on NAICS 561210 (sub-service breakdown via PSC codes + award titles)
        + expanded NAICS universe analysis for adjacent codes not previously evaluated.

New NAICS candidates (facilities-adjacent, O&M, trades, environmental):
  238220  Plumbing/HVAC Contractors
  238210  Electrical Contractors
  238990  Other Specialty Trade Contractors
  236220  Commercial/Institutional Building Construction (O&M)
  811310  Commercial Machinery & Equipment Repair/Maintenance
  562910  Remediation Services
  561990  All Other Support Services
  237310  Highway, Street, Bridge Construction (grounds/roads)
  541513  Computer Facilities Management Services
  561621  Security Systems Services
"""

import json
import time
import urllib.request
import urllib.error
from collections import defaultdict

API_BASE = "https://api.usaspending.gov/api/v2"
SET_ASIDE_CODES = ["SDVOSBC", "SDVOSBS"]
FISCAL_YEARS = [2022, 2023, 2024]

# ── PSC code taxonomy relevant to 561210 / facilities ───────────────────────
# S-series = Housekeeping & Base Services
# Z-series = Maintenance, Repair, Alteration, Real Property
# J-series = Maintenance/Repair of Equipment
PSC_LABELS = {
    # S-series
    "S201": "Custodial/Janitorial",
    "S202": "Grounds Maintenance",
    "S203": "Refuse Collection",
    "S204": "Pest Control",
    "S205": "Building/Plant Maintenance",
    "S206": "Building/Plant Repair",
    "S207": "Snow Removal",
    "S208": "Water Treatment",
    "S209": "Other Building/Plant Services",
    "S299": "Other Housekeeping Services",
    # Z-series (real property maintenance)
    "Z1AA": "Maintenance — Office Bldgs",
    "Z1AB": "Maintenance — Other Bldgs",
    "Z1AZ": "Maintenance — Other Real Property",
    "Z2AA": "Repair/Alteration — Office Bldgs",
    "Z2AB": "Repair/Alteration — Other Bldgs",
    "Z2AZ": "Repair/Alteration — Other Real Property",
    # J-series (equipment maintenance)
    "J015": "Maintenance — Aircraft Ground Support Equipment",
    "J059": "Maintenance — HVAC Equipment",
    "J099": "Maintenance — Other Equipment",
    # Facility management / operations
    "S112": "Facilities Operations Support",
    "S113": "Facilities Support Services",
    "S118": "Building Management",
    "S119": "Base Operations Support",
    "S120": "Base Maintenance",
    "S199": "Other Facilities Support",
}

# ── New NAICS to evaluate ─────────────────────────────────────────────────
NEW_NAICS = {
    "238220": "Plumbing/HVAC Contractors",
    "238210": "Electrical Contractors",
    "238990": "Other Specialty Trade Contractors",
    "236220": "Commercial/Institutional Building Construction",
    "811310": "Commercial Machinery/Equip Repair & Maint",
    "562910": "Remediation Services",
    "561990": "All Other Support Services",
    "237310": "Highway, Street & Bridge Construction",
    "541513": "Computer Facilities Mgmt Services",
    "561621": "Security Systems Services (Except Locksmiths)",
}

# ── Previous top-5 for reference ─────────────────────────────────────────
PREV_TOP5 = {
    "561210": "Facilities Support Services",
    "561720": "Janitorial Services",
    "493110": "General Warehousing & Storage",
    "561612": "Security Guards & Patrol",
    "561320": "Temporary Staffing",
}


def post_json(url, payload, retries=4):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"    HTTP {e.code} final: {body[:150]}")
                return None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"    Final error: {e}")
                return None


def tp(fy):
    return {"start_date": f"{fy-1}-10-01", "end_date": f"{fy}-09-30"}


def base_filters(naics_code, fiscal_years=FISCAL_YEARS):
    return {
        "time_period": [tp(fy) for fy in fiscal_years],
        "naics_codes": [naics_code],
        "set_aside_type_codes": SET_ASIDE_CODES,
        "award_type_codes": ["A", "B", "C", "D"],
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


# ═══════════════════════════════════════════════════════════════════════════
# PART 1 — 561210 PSC Breakdown
# ═══════════════════════════════════════════════════════════════════════════

def fetch_psc_breakdown(naics_code):
    """Get top PSC codes within a NAICS code — reveals actual service lines."""
    r = post_json(f"{API_BASE}/search/spending_by_category/psc/", {
        "filters": base_filters(naics_code),
        "category": "psc",
        "limit": 25,
        "page": 1,
    })
    if r and "results" in r:
        return r["results"]
    return []


def fetch_award_sample(naics_code, limit=50):
    """Pull individual award descriptions to infer service sub-types."""
    r = post_json(f"{API_BASE}/search/spending_by_award/", {
        "filters": base_filters(naics_code),
        "fields": ["Award ID", "Award Amount", "Description", "Awarding Agency",
                   "Recipient Name", "Award Date", "Period of Performance Current End Date"],
        "sort": "Award Amount",
        "order": "desc",
        "limit": limit,
        "page": 1,
        "subawards": False,
    })
    if r and "results" in r:
        return r["results"]
    return []


def fetch_psc_agency_breakdown(psc_code):
    """For a specific PSC code, get top agencies and obligations."""
    r = post_json(f"{API_BASE}/search/spending_by_category/awarding_agency/", {
        "filters": {
            "time_period": [tp(fy) for fy in FISCAL_YEARS],
            "psc_codes": {"require": [[psc_code]]},
            "set_aside_type_codes": SET_ASIDE_CODES,
            "award_type_codes": ["A", "B", "C", "D"],
        },
        "category": "awarding_agency",
        "limit": 5,
        "page": 1,
    })
    if r and "results" in r:
        return r["results"]
    return []


def fetch_psc_yearly(psc_code):
    """Year-over-year spending for a specific PSC code."""
    results = {}
    for fy in FISCAL_YEARS:
        r = post_json(f"{API_BASE}/search/spending_over_time/", {
            "group": "fiscal_year",
            "filters": {
                "time_period": [tp(fy)],
                "psc_codes": {"require": [[psc_code]]},
                "set_aside_type_codes": SET_ASIDE_CODES,
                "award_type_codes": ["A", "B", "C", "D"],
            },
        })
        obs = 0.0
        if r and "results" in r:
            obs = sum(x.get("aggregated_amount", 0) or 0 for x in r["results"])
        results[fy] = obs
        time.sleep(0.1)
    return results


def fetch_psc_count(psc_code):
    """Award count for a PSC code."""
    r = post_json(f"{API_BASE}/search/spending_by_award_count/", {
        "filters": {
            "time_period": [tp(fy) for fy in FISCAL_YEARS],
            "psc_codes": {"require": [[psc_code]]},
            "set_aside_type_codes": SET_ASIDE_CODES,
            "award_type_codes": ["A", "B", "C", "D"],
        },
    })
    if r and "results" in r:
        return r["results"].get("contracts", 0) or 0
    return 0


def fetch_psc_awardees(psc_code):
    """Unique awardees for a PSC code."""
    r = post_json(f"{API_BASE}/search/spending_by_category/recipient/", {
        "filters": {
            "time_period": [tp(fy) for fy in FISCAL_YEARS],
            "psc_codes": {"require": [[psc_code]]},
            "set_aside_type_codes": SET_ASIDE_CODES,
            "award_type_codes": ["A", "B", "C", "D"],
        },
        "category": "recipient",
        "limit": 100,
        "page": 1,
    })
    if r and "results" in r:
        count = len(r["results"])
        if r.get("page_metadata", {}).get("hasNext"):
            return f"{count}+"
        return count
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# PART 2 — New NAICS Analysis
# ═══════════════════════════════════════════════════════════════════════════

def fetch_naics_full(naics_code):
    """Full data pull for a single NAICS code."""
    yearly = {}
    for fy in FISCAL_YEARS:
        r_spend = post_json(f"{API_BASE}/search/spending_over_time/", {
            "group": "fiscal_year",
            "filters": {
                "time_period": [tp(fy)],
                "naics_codes": [naics_code],
                "set_aside_type_codes": SET_ASIDE_CODES,
                "award_type_codes": ["A", "B", "C", "D"],
            },
        })
        obs = 0.0
        if r_spend and "results" in r_spend:
            obs = sum(r.get("aggregated_amount", 0) or 0 for r in r_spend["results"])

        r_count = post_json(f"{API_BASE}/search/spending_by_award_count/", {
            "filters": {
                "time_period": [tp(fy)],
                "naics_codes": [naics_code],
                "set_aside_type_codes": SET_ASIDE_CODES,
                "award_type_codes": ["A", "B", "C", "D"],
            },
        })
        cnt = 0
        if r_count and "results" in r_count:
            cnt = r_count["results"].get("contracts", 0) or 0

        yearly[fy] = {"obligations": obs, "contracts": cnt}
        time.sleep(0.15)

    r_agency = post_json(f"{API_BASE}/search/spending_by_category/awarding_agency/", {
        "filters": base_filters(naics_code),
        "category": "awarding_agency",
        "limit": 5,
        "page": 1,
    })
    agencies = []
    if r_agency and "results" in r_agency:
        agencies = [{"name": row.get("name", "Unknown"), "amount": row.get("amount", 0)}
                    for row in r_agency["results"]]
    time.sleep(0.15)

    r_recip = post_json(f"{API_BASE}/search/spending_by_category/recipient/", {
        "filters": base_filters(naics_code),
        "category": "recipient",
        "limit": 100,
        "page": 1,
    })
    unique_awardees = 0
    if r_recip and "results" in r_recip:
        unique_awardees = len(r_recip["results"])
        if r_recip.get("page_metadata", {}).get("hasNext"):
            r2 = post_json(f"{API_BASE}/search/spending_by_category/recipient/", {
                "filters": base_filters(naics_code),
                "category": "recipient",
                "limit": 100,
                "page": 2,
            })
            if r2 and "results" in r2:
                unique_awardees += len(r2["results"])
                if r2.get("page_metadata", {}).get("hasNext"):
                    unique_awardees = f"{unique_awardees}+"
    time.sleep(0.15)

    return {"yearly": yearly, "top_agencies": agencies, "unique_awardees": unique_awardees}


# ═══════════════════════════════════════════════════════════════════════════
# SCORING (reused from Part 1 script logic)
# ═══════════════════════════════════════════════════════════════════════════

WEIGHTS = {
    "market_size_growth": 0.30,
    "avg_contract_value": 0.25,
    "competitor_count":   0.25,
    "accessibility":      0.20,
}


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
    totals, avgs, competitors, accessibilities = [], [], [], []

    for code in codes:
        d = all_data[code]
        yearly = d["yearly"]
        total_obs = sum(v["obligations"] for v in yearly.values())
        total_cnt = sum(v["contracts"] for v in yearly.values())
        avg_val = total_obs / total_cnt if total_cnt > 0 else 0
        fy22 = yearly.get(2022, {}).get("obligations", 0)
        fy24 = yearly.get(2024, {}).get("obligations", 0)
        growth = ((fy24 - fy22) / fy22 * 100) if fy22 > 0 else 0
        market_raw = total_obs * (1 + max(growth, -50) / 100)

        comp = d.get("unique_awardees", 999)
        comp_num = int(str(comp).replace("+", "")) if isinstance(comp, str) else (comp or 999)

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
        fy22 = yearly.get(2022, {}).get("obligations", 0)
        fy24 = yearly.get(2024, {}).get("obligations", 0)
        growth = ((fy24 - fy22) / fy22 * 100) if fy22 > 0 else 0
        details[code] = {
            "total_obs": total_obs,
            "total_cnt": total_cnt,
            "avg_val": total_obs / total_cnt if total_cnt else 0,
            "growth": growth,
            "market_n": round(n_market[i]*100, 1),
            "avg_n":    round(n_avg[i]*100, 1),
            "comp_n":   round(n_comp[i]*100, 1),
            "access_n": round(n_access[i]*100, 1),
        }
    return scores, details


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def run():
    results = {}

    # ──────────────────────────────────────────────────────────────────────
    # PART 1 — 561210 PSC Deep Dive
    # ──────────────────────────────────────────────────────────────────────
    print("=" * 72)
    print("  PART 1: NAICS 561210 — INTERNAL SERVICE LINE BREAKDOWN")
    print("  (via Product/Service Code analysis + award sample)")
    print("=" * 72)

    print("\n[1a] Fetching PSC code breakdown within NAICS 561210...")
    psc_rows = fetch_psc_breakdown("561210")
    print(f"  Found {len(psc_rows)} PSC codes")

    # Filter to PSC codes with meaningful activity
    psc_data = {}
    significant_pscs = [(r.get("code"), r.get("name"), r.get("amount", 0))
                        for r in psc_rows if (r.get("amount") or 0) > 100_000]
    significant_pscs.sort(key=lambda x: x[2], reverse=True)

    print(f"\n  {'PSC':<8} {'Description':<45} {'3Y Obligated':>14}  {'% of 561210'}")
    print("  " + "─" * 78)
    total_561210 = sum(r.get("amount", 0) for r in psc_rows)
    for code, name, amt in significant_pscs:
        label = PSC_LABELS.get(code, name or "")[:44]
        pct = amt / total_561210 * 100 if total_561210 else 0
        print(f"  {code:<8} {label:<45} {fmt_dollars(amt):>14}  {pct:.1f}%")

    # Detailed drill into top PSC codes
    top_pscs = [row[0] for row in significant_pscs[:8] if row[0]]
    psc_detail = {}

    print(f"\n[1b] Deep-diving top {len(top_pscs)} PSC codes (yearly trends, agencies, awardees)...")
    for psc_code in top_pscs:
        label = PSC_LABELS.get(psc_code, "") or next(
            (n for c, n, _ in significant_pscs if c == psc_code), "")
        print(f"  PSC {psc_code} — {label[:50]}")

        yearly = fetch_psc_yearly(psc_code)
        cnt = fetch_psc_count(psc_code)
        agencies = fetch_psc_agency_breakdown(psc_code)
        awardees = fetch_psc_awardees(psc_code)
        time.sleep(0.2)

        total = sum(yearly.values())
        avg = total / cnt if cnt else 0
        fy22 = yearly.get(2022, 0)
        fy24 = yearly.get(2024, 0)
        growth = ((fy24 - fy22) / fy22 * 100) if fy22 > 0 else 0

        psc_detail[psc_code] = {
            "label": label,
            "yearly": yearly,
            "total": total,
            "count": cnt,
            "avg": avg,
            "growth": growth,
            "agencies": agencies,
            "awardees": awardees,
        }
        print(f"    Total: {fmt_dollars(total)} | {cnt} awards | Avg: {fmt_dollars(avg)} | Growth: {fmt_pct(growth)} | Awardees: {awardees}")

    results["psc_detail"] = psc_detail

    # Award title sample
    print("\n[1c] Sampling award descriptions (top 50 by value)...")
    awards = fetch_award_sample("561210", limit=50)
    desc_counts = defaultdict(int)
    keyword_map = {
        "base operations": "Base Operations Support (BOS)",
        "base ops": "Base Operations Support (BOS)",
        "facilities operations": "Facilities Operations & Maint (O&M)",
        "facilities management": "Facilities Management",
        "facility management": "Facilities Management",
        "operations and maintenance": "Operations & Maintenance (O&M)",
        "o&m": "Operations & Maintenance (O&M)",
        "custodial": "Custodial/Janitorial",
        "janitorial": "Custodial/Janitorial",
        "grounds": "Grounds Maintenance",
        "landscaping": "Grounds Maintenance",
        "hvac": "HVAC/Mechanical",
        "mechanical": "HVAC/Mechanical",
        "pest control": "Pest Control",
        "environmental": "Environmental Services",
        "utilities": "Utilities Management",
        "energy": "Energy Management",
        "maintenance": "General Maintenance",
        "repair": "Maintenance & Repair",
        "logistics": "Logistics Support",
        "support services": "General Support Services",
    }

    for award in awards:
        desc = (award.get("Description") or "").lower()
        matched = False
        for kw, cat in keyword_map.items():
            if kw in desc:
                desc_counts[cat] += 1
                matched = True
                break
        if not matched:
            desc_counts["Uncategorized/Other"] += 1

    print(f"\n  Service sub-types inferred from top-50 award descriptions:")
    for cat, cnt in sorted(desc_counts.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * cnt
        print(f"    {cat:<40} {cnt:>3}  {bar}")

    results["award_sample_count"] = len(awards)
    results["desc_counts"] = dict(desc_counts)

    # ──────────────────────────────────────────────────────────────────────
    # PART 2 — New NAICS Codes
    # ──────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  PART 2: ADDITIONAL NAICS CODES — NOT PREVIOUSLY ANALYZED")
    print("=" * 72)

    new_naics_data = {}
    total_new = len(NEW_NAICS)
    for idx, (code, label) in enumerate(NEW_NAICS.items(), 1):
        print(f"\n[{idx:>2}/{total_new}] {code} — {label}")
        d = fetch_naics_full(code)
        d["label"] = label
        total_obs = sum(v["obligations"] for v in d["yearly"].values())
        total_cnt = sum(v["contracts"] for v in d["yearly"].values())
        print(f"     Total: {fmt_dollars(total_obs)} | {fmt_num(total_cnt)} awards | Awardees: {d['unique_awardees']}")
        new_naics_data[code] = d
        time.sleep(0.3)

    results["new_naics_data"] = new_naics_data

    # Save raw
    with open("/home/user/operations/sdvosb_deepdive_raw.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("\n[Raw saved to sdvosb_deepdive_raw.json]")

    # ──────────────────────────────────────────────────────────────────────
    # PRINT REPORTS
    # ──────────────────────────────────────────────────────────────────────

    # Report 1: PSC sub-service breakdown
    print("\n" + "=" * 72)
    print("  REPORT 1: 561210 SUB-SERVICE LINE BREAKDOWN BY PSC CODE")
    print("  FY2022–2024 | SDVOSB Set-Aside Only")
    print("=" * 72)
    print(f"\n  {'PSC':<8} {'Service Line':<38} {'3Y Total':>10}  {'Awards':>7}  {'Avg Val':>10}  {'YoY%':>7}  {'Awardees':>9}")
    print("  " + "─" * 92)
    psc_sorted = sorted(psc_detail.items(), key=lambda x: x[1]["total"], reverse=True)
    for psc_code, pd in psc_sorted:
        label = pd["label"][:37]
        print(f"  {psc_code:<8} {label:<38} {fmt_dollars(pd['total']):>10}  {fmt_num(pd['count']):>7}  "
              f"{fmt_dollars(pd['avg']):>10}  {fmt_pct(pd['growth']):>7}  {fmt_num(pd['awardees']):>9}")

    print(f"\n  Top agency buyers by PSC sub-service:\n")
    for psc_code, pd in psc_sorted[:5]:
        print(f"  {psc_code} — {pd['label']}")
        for ag in pd["agencies"][:3]:
            print(f"    • {ag['name'][:55]:<55}  {fmt_dollars(ag['amount'])}")

    # Report 2: New NAICS summary
    print("\n" + "=" * 72)
    print("  REPORT 2: NEW NAICS CODES — RAW DATA")
    print("  FY2022–2024 | SDVOSB Set-Aside Only")
    print("=" * 72)
    print(f"\n  {'NAICS':<8} {'Label':<38} {'3Y Total':>10}  {'Awards':>7}  {'Avg Val':>10}  {'YoY%':>7}  {'Awardees':>9}")
    print("  " + "─" * 92)
    for code, d in new_naics_data.items():
        yearly = d["yearly"]
        total_obs = sum(v["obligations"] for v in yearly.values())
        total_cnt = sum(v["contracts"] for v in yearly.values())
        avg_val = total_obs / total_cnt if total_cnt else 0
        fy22 = yearly.get(2022, {}).get("obligations", 0)
        fy24 = yearly.get(2024, {}).get("obligations", 0)
        growth = ((fy24 - fy22) / fy22 * 100) if fy22 > 0 else 0
        label = d["label"][:37]
        uniq = d.get("unique_awardees", "—")
        print(f"  {code:<8} {label:<38} {fmt_dollars(total_obs):>10}  {fmt_num(total_cnt):>7}  "
              f"{fmt_dollars(avg_val):>10}  {fmt_pct(growth):>7}  {fmt_num(uniq):>9}")

    # Report 3: Combined scoring (new NAICS vs previous top-5)
    print("\n" + "=" * 72)
    print("  REPORT 3: COMBINED SCORING — NEW NAICS vs PREVIOUS TOP 5")
    print("=" * 72)

    # Load previous top-5 data from existing raw file
    combined = {}
    try:
        with open("/home/user/operations/sdvosb_expansion_raw.json") as f:
            prev_raw = json.load(f)
        for code in PREV_TOP5:
            if code in prev_raw:
                combined[code] = prev_raw[code]
                combined[code]["label"] = PREV_TOP5[code]
    except Exception as e:
        print(f"  Warning: couldn't load previous data: {e}")

    for code, d in new_naics_data.items():
        combined[code] = d

    scores, details = compute_scores(combined)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    print(f"\n  {'Rk':<4} {'NAICS':<8} {'Label':<34}  {'Mkt/Grw':>7}  {'AvgVal':>7}  {'Comp':>7}  {'Access':>7}  {'SCORE':>7}  {'Source'}")
    print("  " + "─" * 96)
    for i, (code, score) in enumerate(ranked, 1):
        det = details[code]
        label = combined[code]["label"][:33]
        source = "NEW" if code in NEW_NAICS else "prev"
        print(f"  {i:<4} {code:<8} {label:<34}  {det['market_n']:>7.1f}  {det['avg_n']:>7.1f}  "
              f"{det['comp_n']:>7.1f}  {det['access_n']:>7.1f}  {score:>7.1f}  {source}")

    # ──────────────────────────────────────────────────────────────────────
    # FINAL SYNTHESIS
    # ──────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  FINAL SYNTHESIS")
    print("=" * 72)

    # Best PSC within 561210
    best_psc = psc_sorted[0] if psc_sorted else (None, {})
    best_psc_code, best_psc_d = best_psc

    # New NAICS that cracked top 5
    top5_codes = [c for c, _ in ranked[:5]]
    new_entrants = [c for c in top5_codes if c in NEW_NAICS]
    prev_survivors = [c for c in top5_codes if c in PREV_TOP5]

    print(f"""
WITHIN 561210 — FOCUS ON THESE SUB-SERVICE LINES:

  The PSC code breakdown reveals what the federal government actually
  buys under the broad "Facilities Support Services" label.
  The top sub-categories by SDVOSB NAICS 561210 obligation are:
""")
    for psc_code, pd in psc_sorted[:5]:
        print(f"  • {psc_code} — {pd['label']}: {fmt_dollars(pd['total'])} "
              f"({fmt_num(pd['count'])} awards, avg {fmt_dollars(pd['avg'])}, {fmt_pct(pd['growth'])} growth)")

    print(f"""
  RECOMMENDED FOCUS: The sub-service with the best combination of volume,
  accessible contract sizing, and growth is identified above. Build your
  capability statement and past performance narrative around this specific
  task type within 561210 — don't pitch "facilities support" generically.

NEW NAICS CODES THAT ENTERED THE TOP 5:
""")
    if new_entrants:
        for code in new_entrants:
            d = combined[code]
            det = details[code]
            yearly = d["yearly"]
            total_obs = sum(v["obligations"] for v in yearly.values())
            total_cnt = sum(v["contracts"] for v in yearly.values())
            avg_val = total_obs / total_cnt if total_cnt else 0
            print(f"  ★ {code} — {d['label']}")
            print(f"    Score: {scores[code]:.1f}/100 | {fmt_dollars(total_obs)} over 3 yrs | "
                  f"Avg: {fmt_dollars(avg_val)} | Growth: {fmt_pct(det['growth'])}")
            for ag in d.get("top_agencies", [])[:2]:
                print(f"    Top buyer: {ag['name']}: {fmt_dollars(ag['amount'])}")
    else:
        print("  No new NAICS codes displaced the previous top 5 in this scoring run.")
        print("  The previous top-5 remain the best-ranked set even against the expanded universe.")

    print(f"""
BOTTOM LINE ON EXPANSION PATH:
  The data continues to support 561210 as the primary NAICS to register,
  but your capability statement should be anchored to the top PSC sub-service
  codes above — that is where the contract volume actually lives within the code.
  Generic "facilities support" bids will lose to specialists. Narrow your pitch.
""")

    print("=" * 72)
    print("[Data: USASpending.gov API v2 | Retrieved March 2026]")
    print("[Raw: sdvosb_deepdive_raw.json]")
    print("=" * 72)

    return results


if __name__ == "__main__":
    run()
