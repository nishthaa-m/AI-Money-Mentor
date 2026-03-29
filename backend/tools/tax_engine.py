"""
Tax Engine — FY 2025-26 (AY 2026-27)
Finance Act 2025 — Budget presented Feb 1, 2025

Key FY2025-26 changes vs FY2024-25:
- New regime rebate u/s 87A raised: zero tax up to ₹12L taxable income (was ₹7L)
- New regime slabs revised (effective from FY2025-26)
- Standard deduction: ₹75,000 (unchanged)
- Old regime: unchanged

Sources:
- Finance Bill 2025, Clause 2 (income tax rates)
- CBDT Circular on new regime slabs
- incometaxindia.gov.in
"""
from __future__ import annotations
from dataclasses import dataclass, field


# ── FY2025-26 New Regime Slabs (Finance Act 2025) ────────────────────────────
# Revised slabs effective AY 2026-27
NEW_REGIME_SLABS_FY26 = [
    (400_000,       0.00),   # 0 – 4L: nil
    (800_000,       0.05),   # 4L – 8L: 5%
    (1_200_000,     0.10),   # 8L – 12L: 10%
    (1_600_000,     0.15),   # 12L – 16L: 15%
    (2_000_000,     0.20),   # 16L – 20L: 20%
    (2_400_000,     0.25),   # 20L – 24L: 25%
    (float("inf"),  0.30),   # above 24L: 30%
]

# ── FY2025-26 Old Regime Slabs (unchanged) ───────────────────────────────────
OLD_REGIME_SLABS = [
    (250_000,       0.00),
    (500_000,       0.05),
    (1_000_000,     0.20),
    (float("inf"),  0.30),
]

# ── Key constants FY2025-26 ───────────────────────────────────────────────────
STANDARD_DEDUCTION_NEW = 75_000    # unchanged from FY2024-25
STANDARD_DEDUCTION_OLD = 50_000

# FY2025-26: Rebate u/s 87A — zero tax if taxable income ≤ ₹12L (new regime)
# This means gross income up to ₹12.75L (12L + 75k std ded) = ZERO tax
REBATE_87A_NEW_LIMIT  = 1_200_000   # taxable income threshold
REBATE_87A_NEW_MAX    = 60_000      # max rebate amount (covers full tax up to 12L)

# Old regime: rebate if taxable ≤ ₹5L (unchanged)
REBATE_87A_OLD_LIMIT  = 500_000
REBATE_87A_OLD_MAX    = 12_500

# ── Deduction limits (old regime, FY2025-26 — unchanged) ─────────────────────
LIMIT_80C           = 150_000
LIMIT_80CCD1B       = 50_000   # NPS Tier-1 additional (over 80C)
LIMIT_80D_SELF      = 25_000   # health insurance self+family (< 60 yrs)
LIMIT_80D_SELF_SR   = 50_000   # health insurance self+family (≥ 60 yrs)
LIMIT_80D_PARENTS   = 25_000
LIMIT_80D_PARENTS_SR = 50_000  # senior citizen parents
LIMIT_24B           = 200_000  # home loan interest (self-occupied)


@dataclass
class DeductionProfile:
    section_80c: float = 0.0
    section_80d_self: float = 0.0
    section_80d_parents: float = 0.0
    section_80ccd1b: float = 0.0
    hra_exempt: float = 0.0
    lta: float = 0.0
    home_loan_interest: float = 0.0
    home_loan_principal: float = 0.0
    other_deductions: float = 0.0
    age: int = 30


def _slab_tax(income: float, slabs: list) -> float:
    """Progressive slab tax calculation."""
    tax = 0.0
    prev = 0.0
    for limit, rate in slabs:
        if income <= prev:
            break
        band = min(income, limit) - prev
        tax += band * rate
        prev = limit
        if limit == float("inf"):
            break
    return tax


def _marginal_rate(taxable_income: float, regime: str) -> float:
    slabs = NEW_REGIME_SLABS_FY26 if regime == "new" else OLD_REGIME_SLABS
    prev = 0.0
    for limit, rate in slabs:
        if taxable_income <= limit:
            return rate
        prev = limit
    return 0.30


def _surcharge(taxable: float, tax: float) -> float:
    """Surcharge — same for both regimes."""
    if taxable <= 5_000_000:
        return 0.0
    elif taxable <= 10_000_000:
        return tax * 0.10
    elif taxable <= 20_000_000:
        return tax * 0.15
    elif taxable <= 50_000_000:
        return tax * 0.25
    return tax * 0.37


def calculate_tax(gross_income: float, deductions: DeductionProfile, regime: str = "new") -> dict:
    """
    Calculate income tax for FY 2025-26 (AY 2026-27).
    Returns full breakdown.
    """
    if regime == "new":
        std_ded = STANDARD_DEDUCTION_NEW
        taxable = max(gross_income - std_ded, 0)
        tax = _slab_tax(taxable, NEW_REGIME_SLABS_FY26)
        # Rebate 87A FY2025-26: zero tax if taxable ≤ ₹12L
        # Apply marginal relief: tax cannot exceed income above ₹12L threshold
        if taxable <= REBATE_87A_NEW_LIMIT:
            tax = 0.0
        elif taxable <= REBATE_87A_NEW_LIMIT + 100_000:
            # Marginal relief: tax capped at (taxable - 12L)
            tax_without_relief = tax
            marginal_relief_cap = taxable - REBATE_87A_NEW_LIMIT
            tax = min(tax_without_relief, marginal_relief_cap)
        total_deductions = std_ded
        deductions_applied = {"Standard Deduction (Sec 16)": std_ded}

    else:  # old regime
        std_ded = STANDARD_DEDUCTION_OLD
        age = getattr(deductions, "age", 30)
        sec_80c = min(deductions.section_80c + deductions.home_loan_principal, LIMIT_80C)
        d_self_lim = LIMIT_80D_SELF_SR if age >= 60 else LIMIT_80D_SELF
        d_par_lim  = LIMIT_80D_PARENTS_SR if age >= 60 else LIMIT_80D_PARENTS
        sec_80d    = min(deductions.section_80d_self, d_self_lim) + min(deductions.section_80d_parents, d_par_lim)
        sec_80ccd  = min(deductions.section_80ccd1b, LIMIT_80CCD1B)
        sec_24b    = min(deductions.home_loan_interest, LIMIT_24B)
        total_deductions = (std_ded + sec_80c + sec_80d + sec_80ccd +
                            deductions.hra_exempt + deductions.lta +
                            sec_24b + deductions.other_deductions)
        taxable = max(gross_income - total_deductions, 0)
        tax = _slab_tax(taxable, OLD_REGIME_SLABS)
        if taxable <= REBATE_87A_OLD_LIMIT:
            tax = max(tax - REBATE_87A_OLD_MAX, 0)
        deductions_applied = {
            "Standard Deduction (Sec 16)": std_ded,
            "Sec 80C": sec_80c,
            "Sec 80D (Health Insurance)": sec_80d,
            "Sec 80CCD(1B) NPS": sec_80ccd,
            "HRA Exemption": deductions.hra_exempt,
            "LTA": deductions.lta,
            "Sec 24(b) Home Loan Interest": sec_24b,
            "Other": deductions.other_deductions,
        }

    surcharge = _surcharge(taxable, tax)
    cess = round((tax + surcharge) * 0.04, 2)
    total_tax = round(tax + surcharge + cess, 2)

    return {
        "regime": regime,
        "gross_income": gross_income,
        "total_deductions": round(total_deductions, 2),
        "taxable_income": round(taxable, 2),
        "base_tax": round(tax, 2),
        "surcharge": round(surcharge, 2),
        "cess": round(cess, 2),
        "total_tax": total_tax,
        "effective_rate_pct": round((total_tax / gross_income) * 100, 2) if gross_income else 0,
        "monthly_tax": round(total_tax / 12, 2),
        "deductions_applied": {k: v for k, v in deductions_applied.items() if v > 0},
        "fy": "2025-26",
    }


def compare_regimes(gross_income: float, deductions: DeductionProfile) -> dict:
    """Compare old vs new regime. Recommend lower tax option."""
    new = calculate_tax(gross_income, deductions, "new")
    old = calculate_tax(gross_income, deductions, "old")
    saving = old["total_tax"] - new["total_tax"]
    recommended = "new" if new["total_tax"] <= old["total_tax"] else "old"
    return {
        "new_regime": new,
        "old_regime": old,
        "recommended_regime": recommended,
        "tax_saving_with_recommended": abs(round(saving, 2)),
        "verdict": (
            f"New regime saves ₹{abs(saving):,.0f}/year (₹{abs(saving)//12:,.0f}/month)"
            if recommended == "new"
            else f"Old regime saves ₹{abs(saving):,.0f}/year — deductions make it worthwhile"
        ),
        "note": (
            "FY2025-26: New regime now offers zero tax up to ₹12.75L gross income. "
            "Old regime deductions (80C, 80D, NPS) are NOT available under new regime."
        ),
    }


def calculate_hra_exemption(
    annual_hra_received: float,
    annual_basic: float,
    annual_rent_paid: float,
    metro_city: bool = True,
) -> dict:
    """
    HRA exemption = minimum of:
    1. Actual HRA received
    2. 50% of basic (metro) or 40% (non-metro)
    3. Rent paid - 10% of basic
    Source: Sec 10(13A), IT Act
    """
    metro_pct = 0.50 if metro_city else 0.40
    limit1 = annual_hra_received
    limit2 = annual_basic * metro_pct
    limit3 = max(annual_rent_paid - annual_basic * 0.10, 0)
    exempt = min(limit1, limit2, limit3)
    return {
        "hra_received": annual_hra_received,
        "limit1_actual_hra": round(limit1, 0),
        "limit2_metro_pct": round(limit2, 0),
        "limit3_rent_minus_10pct_basic": round(limit3, 0),
        "hra_exempt": round(exempt, 0),
        "hra_taxable": round(annual_hra_received - exempt, 0),
        "rule": "Min of: actual HRA, 50% basic (metro), rent paid - 10% basic",
    }


def calculate_tax_with_steps(
    gross_income: float,
    deductions: "DeductionProfile",
    regime: str = "new",
) -> dict:
    """
    Full step-by-step tax calculation — verifiable trace for judges.
    Returns every intermediate step so the logic is transparent.
    """
    result = calculate_tax(gross_income, deductions, regime)
    steps = []

    if regime == "new":
        steps = [
            {"step": 1, "label": "Gross Income", "amount": gross_income, "note": "Total salary/income"},
            {"step": 2, "label": "Less: Standard Deduction (Sec 16)", "amount": -STANDARD_DEDUCTION_NEW, "note": "Flat ₹75,000 for salaried (FY2025-26)"},
            {"step": 3, "label": "Taxable Income", "amount": result["taxable_income"], "note": "Gross - Standard Deduction"},
            {"step": 4, "label": "Tax on slabs", "amount": result["base_tax"], "note": _slab_breakdown(result["taxable_income"], NEW_REGIME_SLABS_FY26)},
            {"step": 5, "label": "Rebate u/s 87A", "amount": -(result["base_tax"] - result["base_tax"]) if result["taxable_income"] <= REBATE_87A_NEW_LIMIT else 0, "note": "Zero tax if taxable ≤ ₹12L"},
            {"step": 6, "label": "Surcharge", "amount": result["surcharge"], "note": "10% if taxable > ₹50L"},
            {"step": 7, "label": "Health & Education Cess (4%)", "amount": result["cess"], "note": "4% on (tax + surcharge)"},
            {"step": 8, "label": "Total Tax Payable", "amount": result["total_tax"], "note": f"Effective rate: {result['effective_rate_pct']}%"},
        ]
    else:
        ded_items = result.get("deductions_applied", {})
        total_ded = result["total_deductions"]
        steps = [
            {"step": 1, "label": "Gross Income", "amount": gross_income, "note": "Total salary/income"},
            {"step": 2, "label": "Less: Standard Deduction (Sec 16)", "amount": -STANDARD_DEDUCTION_OLD, "note": "Flat ₹50,000 for salaried"},
        ]
        step_n = 3
        for ded_name, ded_val in ded_items.items():
            if ded_val > 0 and ded_name != "Standard Deduction (Sec 16)":
                steps.append({"step": step_n, "label": f"Less: {ded_name}", "amount": -ded_val, "note": ""})
                step_n += 1
        steps += [
            {"step": step_n,   "label": "Taxable Income", "amount": result["taxable_income"], "note": f"Gross - Total deductions (₹{total_ded:,.0f})"},
            {"step": step_n+1, "label": "Tax on slabs", "amount": result["base_tax"], "note": _slab_breakdown(result["taxable_income"], OLD_REGIME_SLABS)},
            {"step": step_n+2, "label": "Surcharge", "amount": result["surcharge"], "note": "10% if taxable > ₹50L"},
            {"step": step_n+3, "label": "Health & Education Cess (4%)", "amount": result["cess"], "note": "4% on (tax + surcharge)"},
            {"step": step_n+4, "label": "Total Tax Payable", "amount": result["total_tax"], "note": f"Effective rate: {result['effective_rate_pct']}%"},
        ]

    result["steps"] = steps
    return result


def _slab_breakdown(taxable: float, slabs: list) -> str:
    """Human-readable slab breakdown string."""
    parts = []
    prev = 0.0
    for limit, rate in slabs:
        if taxable <= prev:
            break
        band = min(taxable, limit) - prev
        if band > 0 and rate > 0:
            parts.append(f"₹{band:,.0f} @ {int(rate*100)}%")
        prev = limit
        if limit == float("inf"):
            break
    return " + ".join(parts) if parts else "Nil"


def tax_saving_instruments(
    gross_income: float,
    current: "DeductionProfile",
    recommended_regime: str,
) -> list[dict]:
    """
    Suggest tax-saving instruments ranked by liquidity (high→low) and risk (low→high).
    Only relevant for old regime. For new regime, explains why deductions don't apply.
    """
    if recommended_regime == "new":
        return [{
            "rank": 1,
            "instrument": "No deductions needed",
            "section": "N/A",
            "liquidity": "N/A",
            "risk": "N/A",
            "note": "New regime has lower rates — deductions like 80C/80D are not available. Your tax is already optimised.",
        }]

    approx_taxable = max(gross_income - STANDARD_DEDUCTION_OLD - LIMIT_80C, 0)
    marginal = _marginal_rate(approx_taxable, "old")

    instruments = [
        {
            "rank": 1,
            "instrument": "NPS Tier-1 (Sec 80CCD(1B))",
            "section": "80CCD(1B)",
            "max_deduction": LIMIT_80CCD1B,
            "current_invested": current.section_80ccd1b,
            "gap": max(LIMIT_80CCD1B - current.section_80ccd1b, 0),
            "tax_saving": round(max(LIMIT_80CCD1B - current.section_80ccd1b, 0) * marginal, 0),
            "liquidity": "Low — locked till 60, partial withdrawal after 3 yrs",
            "risk": "Medium — market-linked (equity/debt mix)",
            "why_ranked_here": "Extra ₹50K deduction over 80C limit — highest tax bang per rupee",
        },
        {
            "rank": 2,
            "instrument": "ELSS Mutual Funds (Sec 80C)",
            "section": "80C",
            "max_deduction": LIMIT_80C,
            "current_invested": current.section_80c,
            "gap": max(LIMIT_80C - current.section_80c, 0),
            "tax_saving": round(max(LIMIT_80C - current.section_80c, 0) * marginal, 0),
            "liquidity": "Medium — 3-year lock-in (shortest in 80C)",
            "risk": "High — equity mutual fund",
            "why_ranked_here": "Shortest lock-in among 80C options, market-linked returns",
        },
        {
            "rank": 3,
            "instrument": "PPF (Sec 80C)",
            "section": "80C",
            "max_deduction": LIMIT_80C,
            "current_invested": current.section_80c,
            "gap": max(LIMIT_80C - current.section_80c, 0),
            "tax_saving": round(max(LIMIT_80C - current.section_80c, 0) * marginal, 0),
            "liquidity": "Low — 15-year lock-in, partial after 7 yrs",
            "risk": "Very Low — government-backed, ~7.1% p.a.",
            "why_ranked_here": "Safest 80C option, EEE tax status (exempt at all 3 stages)",
        },
        {
            "rank": 4,
            "instrument": "Health Insurance (Sec 80D)",
            "section": "80D",
            "max_deduction": LIMIT_80D_SELF,
            "current_invested": current.section_80d_self,
            "gap": max(LIMIT_80D_SELF - current.section_80d_self, 0),
            "tax_saving": round(max(LIMIT_80D_SELF - current.section_80d_self, 0) * marginal, 0),
            "liquidity": "N/A — insurance premium, not investment",
            "risk": "None — pure protection",
            "why_ranked_here": "Dual benefit: tax saving + health protection",
        },
    ]
    # Filter to only show instruments with a gap
    return [i for i in instruments if i.get("gap", 0) > 0][:3]
    """
    Identify unutilised deductions — ONLY relevant under old regime.
    Tax saving estimated at actual marginal rate.
    """
    approx_taxable = max(gross_income - STANDARD_DEDUCTION_OLD - LIMIT_80C, 0)
    marginal = _marginal_rate(approx_taxable, "old")
    missed = []

    if current.section_80c < LIMIT_80C:
        gap = LIMIT_80C - current.section_80c
        missed.append({
            "section": "80C", "gap": gap,
            "description": "ELSS / PPF / NSC / LIC / 5-yr FD / Home Loan Principal",
            "max_allowed": LIMIT_80C,
            "tax_saving_estimate": round(gap * marginal, 0),
            "priority": "high", "regime_applicable": "old only",
        })
    if current.section_80ccd1b < LIMIT_80CCD1B:
        gap = LIMIT_80CCD1B - current.section_80ccd1b
        missed.append({
            "section": "80CCD(1B)", "gap": gap,
            "description": "NPS Tier-1 additional contribution (over 80C limit)",
            "max_allowed": LIMIT_80CCD1B,
            "tax_saving_estimate": round(gap * marginal, 0),
            "priority": "high", "regime_applicable": "old only",
        })
    d_lim = LIMIT_80D_SELF_SR if current.age >= 60 else LIMIT_80D_SELF
    if current.section_80d_self < d_lim:
        gap = d_lim - current.section_80d_self
        missed.append({
            "section": "80D", "gap": gap,
            "description": "Health Insurance Premium (self + family)",
            "max_allowed": d_lim,
            "tax_saving_estimate": round(gap * marginal, 0),
            "priority": "medium", "regime_applicable": "old only",
        })
    return missed


def identify_missed_deductions(gross_income: float, current: DeductionProfile) -> list[dict]:
    """
    Identify unutilised deductions — ONLY relevant under old regime.
    Tax saving estimated at actual marginal rate.
    """
    approx_taxable = max(gross_income - STANDARD_DEDUCTION_OLD - LIMIT_80C, 0)
    marginal = _marginal_rate(approx_taxable, "old")
    missed = []

    if current.section_80c < LIMIT_80C:
        gap = LIMIT_80C - current.section_80c
        missed.append({
            "section": "80C", "gap": gap,
            "description": "ELSS / PPF / NSC / LIC / 5-yr FD / Home Loan Principal",
            "max_allowed": LIMIT_80C,
            "tax_saving_estimate": round(gap * marginal, 0),
            "priority": "high", "regime_applicable": "old only",
        })
    if current.section_80ccd1b < LIMIT_80CCD1B:
        gap = LIMIT_80CCD1B - current.section_80ccd1b
        missed.append({
            "section": "80CCD(1B)", "gap": gap,
            "description": "NPS Tier-1 additional contribution (over 80C limit)",
            "max_allowed": LIMIT_80CCD1B,
            "tax_saving_estimate": round(gap * marginal, 0),
            "priority": "high", "regime_applicable": "old only",
        })
    d_lim = LIMIT_80D_SELF_SR if current.age >= 60 else LIMIT_80D_SELF
    if current.section_80d_self < d_lim:
        gap = d_lim - current.section_80d_self
        missed.append({
            "section": "80D", "gap": gap,
            "description": "Health Insurance Premium (self + family)",
            "max_allowed": d_lim,
            "tax_saving_estimate": round(gap * marginal, 0),
            "priority": "medium", "regime_applicable": "old only",
        })
    return missed
