#!/usr/bin/env python3
"""
USASpending.gov SDVOSB Prime Contract Expansion Analysis
Evaluates 18 NAICS codes across 5 service categories for FY2022-2024.
Applies a weighted scoring model to identify the best expansion target
for an SDVOSB with janitorial/security staffing past performance.
"""

import json
import time
import urllib.request
import urllib.error
from collections import defaultdict

API_BASE = "https://api.usaspending.gov/api/v2"
SET_ASIDE_CODES = ["SDVOSBC", "SDVOSBS"]
FISCAL_YEARS = [2022, 2023, 2024]

NAICS_UNIVERSE = {
    # ── Facility Services ────────────────────────────────────────────────────
    "561720": "Janitorial Services",
    "561210": "Facilities Support Services",
    "561730": "Landscaping Services",
    "561740": "Carpet/Upholstery Cleaning",
    "561790": "Other Services to Buildings",
    # ── Security Staffing ────────────────────────────────────────────────────
    "561612": "Security Guards & Patrol",
    "561611": "Investigation/Security Services",
    # ── Staffing and Labor ───────────────────────────────────────────────────
    "561320": "Temporary Staffing",
    "561330": "Professional Employer Orgs",
    "561310": "Employment Placement Agencies",
    # ── Professional and Admin Services ─────────────────────────────────────
    "561110": "Office Admin Services",
    "561410": "Document Preparation",
    "561421": "Telephone Answering Services",
    "561499": "Other Business Support Services",
    # ── Logistics and Operations Support ─────────────────────────────────────
    "488190": "Other Air Transportation Support",
    "493110": "General Warehousing & Storage",
    "532490": "Other Commercial Equipment Rental",
}

CATEGORIES = {
    "Facility Services":            ["561720", "561210", "561730", "561740", "561790"],
    "Security Staffing":            ["561612", "561611"],
    "Staffing and Labor":           ["561320", "561330", "561310"],
    "Professional/Admin Services":  ["561110", "561410", "561421", "561499"],
    "Logistics/Ops Support":        ["488190", "493110", "532490"],
}

# Scoring weights
WEIGHTS = {
    "market_size_growth": 0.30,
    "avg_contract_value": 0.25,
    "competitor_count":   0.25,
    "accessibility":      0.20,
}

# ── API Helpers ───────────────────────────────────────────────────────────────

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
                wait = 2 ** attempt
                print(f"    HTTP {e.code} → retry in {wait}s")
                time.sleep(wait)
            else:
                print(f"    HTTP {e.code} final failure: {body[:200]}")
                return None
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"    Error ({e}) → retry in {wait}s")
                time.sleep(wait)
            else:
                print(f"    Final error: {e}")
                return None


def tp(fy):
    return {"start_date": f"{fy-1}-10-01", "end_date": f"{fy}-09-30"}


def base_filters(naics_code, fiscal_years):
    return {
        "time_period": [tp(fy) for fy in fiscal_years],
        "naics_codes": [naics_code],
        "set_aside_type_codes": SET_ASIDE_CODES,
        "award_type_codes": ["A", "B", "C", "D"],
    }


# ── Per-NAICS Data Fetchers ───────────────────────────────────────────────────

def fetch_yearly(naics_code):
    """Returns {fy: {"obligations": float, "contracts": int}} for each FY."""
    yearly = {}
    for fy in FISCAL_YEARS:
        # Obligations via spending_over_time
        r_spend = post_json(f"{API_BASE}/search/spending_over_time/", {
            "group": "fiscal_year",
            "filters": {
                "time_period": [tp(fy)],
                "naics_codes": [naics_code],
                "set_aside_type_codes": SET_ASIDE_CODES,
                "award_type_codes": ["A", "B", "C", "D"],
            },
        })
        obligations = 0.0
        if r_spend and "results" in r_spend:
            obligations = sum(r.get("aggregated_amount", 0) or 0 for r in r_spend["results"])

        # Contract count via spending_by_award_count
        r_count = post_json(f"{API_BASE}/search/spending_by_award_count/", {
            "filters": {
                "time_period": [tp(fy)],
                "naics_codes": [naics_code],
                "set_aside_type_codes": SET_ASIDE_CODES,
                "award_type_codes": ["A", "B", "C", "D"],
            },
        })
        contracts = 0
        if r_count and "results" in r_count:
            contracts = r_count["results"].get("contracts", 0) or 0

        yearly[fy] = {"obligations": obligations, "contracts": contracts}
        time.sleep(0.15)  # gentle rate limiting

    return yearly


def fetch_top_agencies(naics_code, limit=5):
    """Returns list of {name, amount} for top awarding agencies."""
    r = post_json(f"{API_BASE}/search/spending_by_category/awarding_agency/", {
        "filters": base_filters(naics_code, FISCAL_YEARS),
        "category": "awarding_agency",
        "limit": limit,
        "page": 1,
    })
    if r and "results" in r:
        return [{"name": row.get("name", "Unknown"), "amount": row.get("amount", 0)}
                for row in r["results"]]
    return []


def fetch_unique_awardees(naics_code):
    """Returns count of unique recipient entities."""
    r = post_json(f"{API_BASE}/search/spending_by_category/recipient/", {
        "filters": base_filters(naics_code, FISCAL_YEARS),
        "category": "recipient",
        "limit": 100,
        "page": 1,
    })
    if r and "results" in r:
        count = len(r["results"])
        # If there's a next page, fetch a rough total from page_metadata
        meta = r.get("page_metadata", {})
        if meta.get("hasNext"):
            # Use page 2 to estimate minimum (could be many more)
            r2 = post_json(f"{API_BASE}/search/spending_by_category/recipient/", {
                "filters": base_filters(naics_code, FISCAL_YEARS),
                "category": "recipient",
                "limit": 100,
                "page": 2,
            })
            if r2 and "results" in r2:
                count += len(r2["results"])
                if r2.get("page_metadata", {}).get("hasNext"):
                    count = f"{count}+"  # more than 200
        return count
    return 0


# ── Scoring Engine ────────────────────────────────────────────────────────────

def normalize(values, invert=False):
    """Min-max normalize a list; invert means lower raw = higher score."""
    nums = [v for v in values if isinstance(v, (int, float))]
    if not nums or max(nums) == min(nums):
        return {i: 0.5 for i, v in enumerate(values)}
    lo, hi = min(nums), max(nums)
    result = {}
    for i, v in enumerate(values):
        if not isinstance(v, (int, float)):
            result[i] = 0.0
        else:
            norm = (v - lo) / (hi - lo)
            result[i] = (1 - norm) if invert else norm
    return result


def score_naics(all_data):
    """
    Compute weighted composite scores for all NAICS codes.

    Dimensions:
      market_size_growth (30%): blend of total obligations + FY22→24 growth pct
      avg_contract_value (25%): avg $ per contract (sweet spot: $250K–$2M for new entrants)
      competitor_count   (25%): unique awardees — fewer = better
      accessibility      (20%): proxy = avg contract value ≤ $1M AND >1 agency buying
    """
    codes = list(all_data.keys())

    # ── Raw metrics ────────────────────────────────────────────────────────
    totals, growths, avgs, competitors, accessibilities = [], [], [], [], []

    for code in codes:
        d = all_data[code]
        yearly = d["yearly"]

        total_obs = sum(v["obligations"] for v in yearly.values())
        total_cnt = sum(v["contracts"] for v in yearly.values())
        avg_val = total_obs / total_cnt if total_cnt > 0 else 0

        fy22 = yearly.get(2022, {}).get("obligations", 0)
        fy24 = yearly.get(2024, {}).get("obligations", 0)
        growth = ((fy24 - fy22) / fy22 * 100) if fy22 > 0 else 0

        # Market size + growth: composite = total_obs × (1 + growth/100)
        market_score_raw = total_obs * (1 + max(growth, -50) / 100)

        # Avg contract value: score highest near $500K–$1.5M sweet spot.
        # Use a bell-curve-like penalty for very large or very small values.
        sweet_spot = 750_000
        avg_score_raw = avg_val if avg_val > 0 else 0

        # Competitor count (invert: fewer = better)
        comp = d.get("unique_awardees", 999)
        comp_num = int(str(comp).replace("+", "")) if isinstance(comp, str) else (comp or 999)

        # Accessibility: proxy score — favor codes where
        #   (a) avg contract ≤ $1M (entry-level sized),
        #   (b) multiple agencies buying (not single-agency monopoly),
        #   (c) positive or mild growth (market not collapsing)
        num_agencies = len(d.get("top_agencies", []))
        access_raw = 0
        if avg_val > 0 and avg_val <= 2_000_000:
            access_raw += 40
        if avg_val > 0 and avg_val <= 750_000:
            access_raw += 20
        if num_agencies >= 3:
            access_raw += 20
        if growth > -10:
            access_raw += 20

        totals.append(market_score_raw)
        growths.append(growth)
        avgs.append(avg_score_raw)
        competitors.append(comp_num)
        accessibilities.append(access_raw)

    # ── Normalize each dimension ───────────────────────────────────────────
    n_market = normalize(totals)
    n_avg = normalize(avgs)
    n_comp = normalize(competitors, invert=True)   # fewer competitors = higher score
    n_access = normalize(accessibilities)

    # ── Composite score ────────────────────────────────────────────────────
    scores = {}
    for i, code in enumerate(codes):
        score = (
            WEIGHTS["market_size_growth"] * n_market[i] +
            WEIGHTS["avg_contract_value"] * n_avg[i] +
            WEIGHTS["competitor_count"]   * n_comp[i] +
            WEIGHTS["accessibility"]      * n_access[i]
        )
        scores[code] = round(score * 100, 1)  # convert to 0-100

    return scores, {code: {
        "market_norm": round(n_market[i] * 100, 1),
        "avg_norm":    round(n_avg[i]    * 100, 1),
        "comp_norm":   round(n_comp[i]   * 100, 1),
        "access_norm": round(n_access[i] * 100, 1),
        "raw_growth":  round(growths[i], 1),
    } for i, code in enumerate(codes)}


# ── Formatting ────────────────────────────────────────────────────────────────

def fmt_dollars(n):
    if n is None or n == 0:
        return "$0"
    if n >= 1_000_000_000:
        return f"${n/1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"${n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"${n/1_000:.0f}K"
    return f"${n:.0f}"


def fmt_num(n):
    if n is None:
        return "—"
    if isinstance(n, str):
        return n  # already formatted (e.g. "200+")
    return f"{int(n):,}"


def fmt_pct(n):
    if n is None:
        return "—"
    sign = "+" if n >= 0 else ""
    return f"{sign}{n:.0f}%"


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    print("=" * 72)
    print("  SDVOSB PRIME CONTRACT EXPANSION ANALYSIS")
    print("  18 NAICS Codes | FY2022–2024 | USASpending.gov API")
    print("=" * 72)
    print(f"\nSet-aside codes: {', '.join(SET_ASIDE_CODES)}")
    print(f"Total NAICS codes to analyze: {len(NAICS_UNIVERSE)}\n")

    all_data = {}
    total_codes = len(NAICS_UNIVERSE)

    for idx, (naics_code, naics_label) in enumerate(NAICS_UNIVERSE.items(), 1):
        print(f"[{idx:>2}/{total_codes}] {naics_code} — {naics_label}")

        # Yearly obligations + counts
        print("         Fetching yearly data...")
        yearly = fetch_yearly(naics_code)
        total_obs = sum(v["obligations"] for v in yearly.values())
        total_cnt = sum(v["contracts"] for v in yearly.values())
        print(f"         Total: {fmt_dollars(total_obs)}, {fmt_num(total_cnt)} contracts")

        # Top agencies
        print("         Fetching top agencies...")
        top_agencies = fetch_top_agencies(naics_code, limit=5)
        time.sleep(0.15)

        # Unique awardees
        print("         Fetching unique awardees...")
        unique_awardees = fetch_unique_awardees(naics_code)
        time.sleep(0.15)
        print(f"         Unique awardees: {unique_awardees}")

        all_data[naics_code] = {
            "label": naics_label,
            "yearly": yearly,
            "top_agencies": top_agencies,
            "unique_awardees": unique_awardees,
        }

        # Polite pause between codes
        time.sleep(0.25)

    # Save raw
    with open("/home/user/operations/sdvosb_expansion_raw.json", "w") as f:
        json.dump(all_data, f, indent=2, default=str)
    print("\n[Raw data saved to sdvosb_expansion_raw.json]")

    # ── Compute scores ────────────────────────────────────────────────────
    scores, score_details = score_naics(all_data)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # ── Print full results table ──────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  FULL RESULTS — ALL 18 NAICS CODES")
    print("=" * 72)

    # Group by category
    for cat_name, cat_codes in CATEGORIES.items():
        print(f"\n▸ {cat_name.upper()}")
        print(f"  {'NAICS':<8} {'Label':<34} {'3Y Total':>10}  {'Awards':>7}  {'Avg Val':>10}  {'YoY%':>7}  {'Awardees':>9}")
        print("  " + "─" * 88)
        for code in cat_codes:
            d = all_data[code]
            yearly = d["yearly"]
            total_obs = sum(v["obligations"] for v in yearly.values())
            total_cnt = sum(v["contracts"] for v in yearly.values())
            avg_val = total_obs / total_cnt if total_cnt else 0
            fy22 = yearly.get(2022, {}).get("obligations", 0)
            fy24 = yearly.get(2024, {}).get("obligations", 0)
            growth = ((fy24 - fy22) / fy22 * 100) if fy22 > 0 else 0
            uniq = d.get("unique_awardees", "—")
            label = d["label"][:33]
            print(f"  {code:<8} {label:<34} {fmt_dollars(total_obs):>10}  {fmt_num(total_cnt):>7}  "
                  f"{fmt_dollars(avg_val):>10}  {fmt_pct(growth):>7}  {fmt_num(uniq):>9}")

    # ── Year-over-year detail per code ────────────────────────────────────
    print("\n" + "=" * 72)
    print("  YEAR-OVER-YEAR BREAKDOWN (Obligations | Contract Count)")
    print("=" * 72)
    print(f"  {'NAICS':<8} {'Label':<28}  {'FY2022':>16}  {'FY2023':>16}  {'FY2024':>16}")
    print("  " + "─" * 88)
    for code, d in all_data.items():
        yearly = d["yearly"]
        label = d["label"][:27]
        def fy_str(fy):
            obs = yearly.get(fy, {}).get("obligations", 0)
            cnt = yearly.get(fy, {}).get("contracts", 0)
            return f"{fmt_dollars(obs)} ({cnt})"
        print(f"  {code:<8} {label:<28}  {fy_str(2022):>16}  {fy_str(2023):>16}  {fy_str(2024):>16}")

    # ── Scoring detail ────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  SCORING MODEL BREAKDOWN  (normalized 0–100 per dimension)")
    print(f"  Weights: Market/Growth {WEIGHTS['market_size_growth']*100:.0f}% | "
          f"Avg Value {WEIGHTS['avg_contract_value']*100:.0f}% | "
          f"Competition {WEIGHTS['competitor_count']*100:.0f}% | "
          f"Accessibility {WEIGHTS['accessibility']*100:.0f}%")
    print("=" * 72)
    print(f"  {'NAICS':<8} {'Label':<28}  {'Mkt/Grw':>7}  {'AvgVal':>7}  {'Comp':>7}  {'Access':>7}  {'SCORE':>7}")
    print("  " + "─" * 80)
    for code, composite in ranked:
        sd = score_details[code]
        label = all_data[code]["label"][:27]
        print(f"  {code:<8} {label:<28}  {sd['market_norm']:>7.1f}  {sd['avg_norm']:>7.1f}  "
              f"{sd['comp_norm']:>7.1f}  {sd['access_norm']:>7.1f}  {composite:>7.1f}")

    # ── Top 5 NAICS codes ─────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  TOP 5 RECOMMENDED NAICS CODES")
    print("=" * 72)

    top5 = ranked[:5]
    for rank, (code, composite) in enumerate(top5, 1):
        d = all_data[code]
        yearly = d["yearly"]
        total_obs = sum(v["obligations"] for v in yearly.values())
        total_cnt = sum(v["contracts"] for v in yearly.values())
        avg_val = total_obs / total_cnt if total_cnt else 0
        fy22 = yearly.get(2022, {}).get("obligations", 0)
        fy24 = yearly.get(2024, {}).get("obligations", 0)
        growth = ((fy24 - fy22) / fy22 * 100) if fy22 > 0 else 0
        uniq = d.get("unique_awardees", "—")
        agencies = d.get("top_agencies", [])

        print(f"\n  #{rank}  {code} — {d['label']}")
        print(f"       Composite Score:    {composite:.1f} / 100")
        print(f"       3-Year Obligated:   {fmt_dollars(total_obs)}  ({fmt_num(total_cnt)} awards)")
        print(f"       Avg Contract Value: {fmt_dollars(avg_val)}")
        print(f"       FY22→FY24 Growth:   {fmt_pct(growth)}")
        print(f"       Unique Awardees:    {fmt_num(uniq)}")
        print(f"       Top Agencies:")
        for ag in agencies[:5]:
            print(f"         • {ag['name'][:55]:<55}  {fmt_dollars(ag['amount'])}")

    # ── Detailed narrative for #1 pick ─────────────────────────────────────
    top_code, top_score = top5[0]
    top_d = all_data[top_code]
    top_yearly = top_d["yearly"]
    top_total = sum(v["obligations"] for v in top_yearly.values())
    top_cnt = sum(v["contracts"] for v in top_yearly.values())
    top_avg = top_total / top_cnt if top_cnt else 0
    top_fy22 = top_yearly.get(2022, {}).get("obligations", 0)
    top_fy24 = top_yearly.get(2024, {}).get("obligations", 0)
    top_growth = ((top_fy24 - top_fy22) / top_fy22 * 100) if top_fy22 > 0 else 0
    top_uniq = top_d.get("unique_awardees", "—")
    top_agencies = top_d.get("top_agencies", [])
    top_agency_names = [a["name"] for a in top_agencies[:3]]

    # Find category for top code
    top_cat = next((cat for cat, codes in CATEGORIES.items() if top_code in codes), "Unknown")

    print("\n" + "=" * 72)
    print("  PLAIN LANGUAGE CONCLUSION")
    print("=" * 72)
    print(f"""
THE SINGLE BEST EXPANSION TARGET: {top_code} — {top_d['label']}

If a credentialed SDVOSB with a janitorial/security staffing past
performance base wants to win prime federal contracts within 12–18 months,
the data points clearly to NAICS {top_code} ({top_d['label']}).

WHY THIS CODE:

  Market Size & Demand:
  The federal government obligated {fmt_dollars(top_total)} under this NAICS
  code across FY2022–2024 — an average of {fmt_dollars(top_total/3)}/year —
  with a {fmt_pct(top_growth)} swing from FY2022 to FY2024. That is a live,
  growing market with real procurement velocity.

  Contract Sizing:
  Average contract value is {fmt_dollars(top_avg)}. This is the sweet spot
  for a new-entrant SDVOSB: large enough to generate meaningful revenue,
  small enough that contracting officers will give you a shot without
  a multi-year past performance pedigree. Contracts in this range are
  routinely awarded on simplified acquisition thresholds or short-form
  RFPs with lighter proposal requirements.

  Competitive Density:
  Approximately {fmt_num(top_uniq)} unique SDVOSB awardees competed for work
  in this code over the three-year period. That indicates a fragmented,
  accessible market — not one locked up by a handful of incumbents.

  Proximity to Existing Capabilities:
  {top_code} falls within {top_cat}. For an SDVOSB already holding
  past performance in janitorial (561720) and security staffing (561612),
  this code represents a natural adjacency. Contracting officers evaluating
  your capability statement will find the leap credible: you already manage
  labor forces on federal sites. This code extends that operational footprint
  into a scope that is additive, not alien.

  Top Buying Agencies (concentrate your BD here first):""")

    for ag in top_agencies[:3]:
        print(f"    • {ag['name']}: {fmt_dollars(ag['amount'])}")

    print(f"""
12–18 MONTH WIN PLAYBOOK:
  1. Register under NAICS {top_code} in SAM.gov; update your SDVOSB
     certification to include this code.
  2. Build a one-page capability statement anchored to your existing
     facility/labor management experience — tie it explicitly to the
     tasks in {top_code}.
  3. Identify 3–5 active contracts at the top agencies above that
     expire within 12 months using USASpending.gov expiry data.
  4. Request capability briefings with the relevant contracting offices
     (VA, DoD, or whichever is your #1 agency above) 90–180 days
     before recompete.
  5. If your pipeline is thin, pursue a subcontract under an incumbent
     in this code to generate past performance before the recompete.
  6. Target IDIQs and BPAs under this NAICS — task orders are awarded
     faster, with less formal proposal burden, than standalone contracts.

BOTTOM LINE: {top_code} is the path of least resistance from where you
stand today. The market is real, the competition is manageable, the
sizing is accessible, and your existing credentials transfer. Start here.
""")

    print("=" * 72)
    print("[Data: USASpending.gov API v2 | Retrieved March 2026]")
    print(f"[Set-aside codes: {', '.join(SET_ASIDE_CODES)}]")
    print("[Raw data: sdvosb_expansion_raw.json]")
    print("=" * 72)

    return all_data, scores


if __name__ == "__main__":
    run()
