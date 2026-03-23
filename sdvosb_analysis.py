#!/usr/bin/env python3
"""
USASpending.gov SDVOSB Consulting Contract Analysis
NAICS: 541611, 541612, 541613, 541614, 541618, 541690
Set-aside: SDVOSBC + SDVOSBS | FY 2022-2024
"""

import json
import time
import urllib.request
import urllib.error

API_BASE = "https://api.usaspending.gov/api/v2"

NAICS_CODES = ["541611", "541612", "541613", "541614", "541618", "541690"]
NAICS_LABELS = {
    "541611": "Administrative/General Mgmt Consulting",
    "541612": "Human Resources Consulting",
    "541613": "Marketing Consulting",
    "541614": "Process/Logistics Consulting",
    "541618": "Other Management Consulting",
    "541690": "Other Scientific/Technical Consulting",
}
FISCAL_YEARS = [2022, 2023, 2024]
# Both competitive and sole-source SDVOSB set-aside codes
SET_ASIDE_CODES = ["SDVOSBC", "SDVOSBS"]


def post_json(url, payload, retries=3):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"  HTTP {e.code} attempt {attempt+1}: {body[:200]}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
        except Exception as e:
            print(f"  Error attempt {attempt+1}: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise


def time_period(fy):
    return {"start_date": f"{fy-1}-10-01", "end_date": f"{fy}-09-30"}


def get_award_count(fiscal_years, naics_codes, set_aside_codes):
    url = f"{API_BASE}/search/spending_by_award_count/"
    payload = {
        "filters": {
            "time_period": [time_period(fy) for fy in fiscal_years],
            "naics_codes": naics_codes,
            "set_aside_type_codes": set_aside_codes,
            "award_type_codes": ["A", "B", "C", "D"],
        }
    }
    return post_json(url, payload)


def get_top_agencies(fiscal_years, naics_codes, set_aside_codes, limit=10):
    url = f"{API_BASE}/search/spending_by_category/awarding_agency/"
    payload = {
        "filters": {
            "time_period": [time_period(fy) for fy in fiscal_years],
            "naics_codes": naics_codes,
            "set_aside_type_codes": set_aside_codes,
            "award_type_codes": ["A", "B", "C", "D"],
        },
        "category": "awarding_agency",
        "limit": limit,
        "page": 1,
    }
    return post_json(url, payload)


def get_spending_over_time(fiscal_years, naics_codes, set_aside_codes):
    url = f"{API_BASE}/search/spending_over_time/"
    payload = {
        "group": "fiscal_year",
        "filters": {
            "time_period": [time_period(fy) for fy in fiscal_years],
            "naics_codes": naics_codes,
            "set_aside_type_codes": set_aside_codes,
            "award_type_codes": ["A", "B", "C", "D"],
        },
    }
    return post_json(url, payload)


def get_award_list(fiscal_years, naics_codes, set_aside_codes, limit=100):
    url = f"{API_BASE}/search/spending_by_award/"
    payload = {
        "filters": {
            "time_period": [time_period(fy) for fy in fiscal_years],
            "naics_codes": naics_codes,
            "set_aside_type_codes": set_aside_codes,
            "award_type_codes": ["A", "B", "C", "D"],
        },
        "fields": ["Award ID", "Recipient Name", "Award Amount", "Awarding Agency",
                   "NAICS Code", "Award Date", "type_of_set_aside"],
        "sort": "Award Amount",
        "order": "desc",
        "limit": limit,
        "page": 1,
        "subawards": False,
    }
    return post_json(url, payload)


def get_naics_breakdown(fiscal_years, naics_codes, set_aside_codes):
    url = f"{API_BASE}/search/spending_by_category/naics/"
    payload = {
        "filters": {
            "time_period": [time_period(fy) for fy in fiscal_years],
            "naics_codes": naics_codes,
            "set_aside_type_codes": set_aside_codes,
            "award_type_codes": ["A", "B", "C", "D"],
        },
        "category": "naics",
        "limit": 20,
        "page": 1,
    }
    return post_json(url, payload)


def get_yearly_count(fy, naics_codes, set_aside_codes):
    url = f"{API_BASE}/search/spending_by_award_count/"
    payload = {
        "filters": {
            "time_period": [time_period(fy)],
            "naics_codes": naics_codes,
            "set_aside_type_codes": set_aside_codes,
            "award_type_codes": ["A", "B", "C", "D"],
        }
    }
    return post_json(url, payload)


def fmt_dollars(n):
    if n is None:
        return "N/A"
    if n >= 1_000_000_000:
        return f"${n/1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"${n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"${n/1_000:.0f}K"
    return f"${n:.0f}"


def fmt_num(n):
    if n is None:
        return "N/A"
    return f"{int(n):,}"


def run():
    print("Querying USASpending.gov API...")
    print(f"NAICS: {', '.join(NAICS_CODES)}")
    print(f"Set-aside codes: {', '.join(SET_ASIDE_CODES)}")
    print(f"Fiscal years: {FISCAL_YEARS}\n")

    # ── 1. Total award count (all 3 years combined) ──────────────────────────
    print("[1/5] Overall award counts (FY2022-2024 combined)...")
    count_all = get_award_count(FISCAL_YEARS, NAICS_CODES, SET_ASIDE_CODES)
    total_awards = count_all.get("results", {}).get("contracts", 0)
    total_idvs = count_all.get("results", {}).get("idvs", 0)
    print(f"  Contracts: {total_awards}, IDVs: {total_idvs}")

    # ── 2. Year-over-year spending + counts ──────────────────────────────────
    print("[2/5] Year-over-year data...")
    yearly_data = {}
    for fy in FISCAL_YEARS:
        fy_spend = get_spending_over_time([fy], NAICS_CODES, SET_ASIDE_CODES)
        fy_count = get_yearly_count(fy, NAICS_CODES, SET_ASIDE_CODES)
        fy_results = fy_spend.get("results", [])
        obligations = sum(r.get("aggregated_amount", 0) or 0 for r in fy_results)
        contracts = fy_count.get("results", {}).get("contracts", 0)
        yearly_data[fy] = {"obligations": obligations, "contracts": contracts}
        print(f"  FY{fy}: {fmt_dollars(obligations)}, {contracts} contracts")

    # ── 3. Top awarding agencies ─────────────────────────────────────────────
    print("[3/5] Top awarding agencies...")
    agency_resp = get_top_agencies(FISCAL_YEARS, NAICS_CODES, SET_ASIDE_CODES, limit=10)
    agencies = agency_resp.get("results", [])
    print(f"  Found {len(agencies)} agencies")

    # ── 4. Sample award list for avg and detail ───────────────────────────────
    print("[4/5] Award list sample (top 100)...")
    awards_resp = get_award_list(FISCAL_YEARS, NAICS_CODES, SET_ASIDE_CODES, limit=100)
    award_list = awards_resp.get("results", [])
    meta = awards_resp.get("page_metadata", {})
    print(f"  Got {len(award_list)} awards in sample; hasNext={meta.get('hasNext')}")

    # ── 5. NAICS breakdown ────────────────────────────────────────────────────
    print("[5/5] NAICS breakdown...")
    naics_resp = get_naics_breakdown(FISCAL_YEARS, NAICS_CODES, SET_ASIDE_CODES)
    naics_rows = naics_resp.get("results", [])
    print(f"  Got {len(naics_rows)} NAICS entries")

    # ── Save raw results ──────────────────────────────────────────────────────
    raw = {
        "count_all": count_all,
        "yearly_data": yearly_data,
        "agency_resp": agency_resp,
        "awards_resp": awards_resp,
        "naics_resp": naics_resp,
    }
    with open("/home/user/operations/sdvosb_raw_results.json", "w") as f:
        json.dump(raw, f, indent=2, default=str)

    # ── Compute totals ────────────────────────────────────────────────────────
    total_obligations = sum(v["obligations"] for v in yearly_data.values())
    total_contracts = sum(v["contracts"] for v in yearly_data.values())
    avg_contract_value = total_obligations / total_contracts if total_contracts > 0 else 0

    # Top 10 largest awards in sample
    amounts = sorted(
        [a.get("Award Amount") or 0 for a in award_list if (a.get("Award Amount") or 0) > 0],
        reverse=True
    )

    # ── PRINT REPORT ─────────────────────────────────────────────────────────
    W = 72
    print("\n" + "=" * W)
    print("  SDVOSB CONSULTING SET-ASIDE CONTRACT ANALYSIS")
    print("  NAICS 541611 / 541612 / 541613 / 541614 / 541618 / 541690")
    print("  Fiscal Years 2022 – 2024  |  Source: USASpending.gov API")
    print("=" * W)

    print("\n┌─────────────────────────────────────────────────────────────────┐")
    print("│  EXECUTIVE SUMMARY                                              │")
    print("├──────────────────────────────────────┬──────────────────────────┤")
    print(f"│  Total Award Count (3 yrs)           │  {fmt_num(total_contracts):<24} │")
    print(f"│  Total Obligated (3 yrs)             │  {fmt_dollars(total_obligations):<24} │")
    print(f"│  Average Contract Value              │  {fmt_dollars(avg_contract_value):<24} │")
    print("└──────────────────────────────────────┴──────────────────────────┘")

    print("\n── YEAR-OVER-YEAR BREAKDOWN ────────────────────────────────────────")
    print(f"  {'FY':<8} {'Contracts':>12}  {'Obligated $':>16}  {'Avg Value':>14}")
    print("  " + "-" * 55)
    for fy in FISCAL_YEARS:
        d = yearly_data[fy]
        cnt = d["contracts"]
        obs = d["obligations"]
        avg = obs / cnt if cnt else 0
        print(f"  FY{fy}   {fmt_num(cnt):>12}  {fmt_dollars(obs):>16}  {fmt_dollars(avg):>14}")
    print("  " + "-" * 55)
    print(f"  {'TOTAL':<8} {fmt_num(total_contracts):>12}  {fmt_dollars(total_obligations):>16}  {fmt_dollars(avg_contract_value):>14}")

    print("\n── TOP 10 AWARDING AGENCIES (FY2022–2024) ──────────────────────────")
    print(f"  {'#':<4} {'Agency':<46} {'Obligated $':>14}  {'Awards':>6}")
    print("  " + "-" * 74)
    for i, row in enumerate(agencies[:10], 1):
        name = (row.get("name") or "Unknown")[:45]
        amt = row.get("amount") or row.get("aggregated_amount") or 0
        cnt = row.get("awarded_count") or row.get("count") or "—"
        cnt_str = fmt_num(cnt) if isinstance(cnt, int) else str(cnt)
        print(f"  {i:<4} {name:<46} {fmt_dollars(amt):>14}  {cnt_str:>6}")

    print("\n── NAICS CODE BREAKDOWN (FY2022–2024) ──────────────────────────────")
    print(f"  {'NAICS':<10} {'Description':<38} {'Obligated $':>14}  {'Awards':>6}")
    print("  " + "-" * 74)
    for row in naics_rows:
        code = str(row.get("code") or "")
        label = (row.get("name") or NAICS_LABELS.get(code, ""))[:37]
        amt = row.get("amount") or row.get("aggregated_amount") or 0
        cnt = row.get("awarded_count") or "—"
        cnt_str = fmt_num(cnt) if isinstance(cnt, int) else str(cnt)
        print(f"  {code:<10} {label:<38} {fmt_dollars(amt):>14}  {cnt_str:>6}")

    if award_list:
        print("\n── TOP 10 LARGEST INDIVIDUAL AWARDS (SAMPLE) ───────────────────────")
        print(f"  {'Recipient':<35} {'Agency':<22} {'Amount':>14}  {'FY'}")
        print("  " + "-" * 80)
        for award in award_list[:10]:
            recip = (award.get("Recipient Name") or "Unknown")[:34]
            agency = (award.get("Awarding Agency") or "")[:21]
            amt = award.get("Award Amount") or 0
            date = award.get("Award Date") or ""
            fy_str = f"FY{date[:4]}" if date else "—"
            print(f"  {recip:<35} {agency:<22} {fmt_dollars(amt):>14}  {fy_str}")

    # ── CONCLUSION ────────────────────────────────────────────────────────────
    print("\n" + "=" * W)
    print("  PLAIN LANGUAGE CONCLUSION")
    print("=" * W)

    # Determine year-over-year trend
    yoy_trend = ""
    if len(FISCAL_YEARS) >= 2:
        first_fy = FISCAL_YEARS[0]
        last_fy = FISCAL_YEARS[-1]
        first_obs = yearly_data[first_fy]["obligations"]
        last_obs = yearly_data[last_fy]["obligations"]
        if first_obs > 0:
            pct_change = (last_obs - first_obs) / first_obs * 100
            direction = "grew" if pct_change > 0 else "fell"
            yoy_trend = f"Obligations {direction} {abs(pct_change):.0f}% from FY{first_fy} to FY{last_fy}."

    annual_avg_contracts = total_contracts / len(FISCAL_YEARS) if FISCAL_YEARS else 0
    annual_avg_obligations = total_obligations / len(FISCAL_YEARS) if FISCAL_YEARS else 0

    verdict = "SUBSTANTIAL" if total_obligations > 500_000_000 else (
        "MODERATE" if total_obligations > 100_000_000 else "LIMITED"
    )

    print(f"""
Over the three fiscal years 2022-2024, the federal government awarded
approximately {fmt_dollars(total_obligations)} in SDVOSB-designated contracts
across the six management and consulting NAICS codes analyzed, comprising
{fmt_num(total_contracts)} individual contract actions.

Annual averages: ~{fmt_num(int(annual_avg_contracts))} contracts/year,
~{fmt_dollars(annual_avg_obligations)}/year obligated.
Average contract value: {fmt_dollars(avg_contract_value)}.

{yoy_trend}

VERDICT: SDVOSB consulting set-aside demand is {verdict}.
""")

    if verdict == "SUBSTANTIAL":
        print("""\
This level of spending represents a well-established set-aside market.
Building a consulting practice around the SDVOSB credential is well-justified:
  • Consistent multi-year demand signals stable agency adoption of SDVOSB set-asides
  • Average contract values suggest meaningful, professional-services-scale engagements
  • Multiple agencies are active buyers, reducing concentration risk
  • Recommendation: PURSUE — the market is deep enough to support pipeline development,
    teaming, and full BD investment in SDVOSB-designated vehicles.\
""")
    elif verdict == "MODERATE":
        print("""\
This level of spending reflects a real but developing set-aside market.
The SDVOSB credential can meaningfully differentiate a consulting practice:
  • Demand exists but is concentrated — identify the top 3-5 agencies and focus there
  • Average contract values indicate substantive engagements, not just micro-purchases
  • Pairing SDVOSB with a GSA Schedule or GWAC vehicle (e.g., OASIS+) will multiply reach
  • Recommendation: PURSUE WITH FOCUS — validate fit with the top agencies shown above
    before committing full BD resources.\
""")
    else:
        print("""\
SDVOSB consulting set-aside volume over this period is relatively limited.
The credential alone is unlikely to carry a consulting practice:
  • Set-aside activity is small relative to the overall consulting contract market
  • Most consulting awards under these NAICS codes are unrestricted competitions
  • Recommendation: USE AS A DIFFERENTIATOR, NOT A FOUNDATION — the SDVOSB designation
    adds competitive advantage in small-business pools and teaming but should be
    combined with other capture strategies (IDIQs, GSA Schedule, subcontracting).\
""")

    print("\n" + "=" * W)
    print("[Data source: USASpending.gov API v2 | Retrieved: March 2026]")
    print("[Set-aside codes: SDVOSBC (competitive) + SDVOSBS (sole source)]")
    print("[Raw results saved to: sdvosb_raw_results.json]")
    print("=" * W)

    return raw


if __name__ == "__main__":
    run()
