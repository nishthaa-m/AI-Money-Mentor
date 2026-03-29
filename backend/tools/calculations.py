"""
Pure calculation engine — no LLM, fully deterministic.
Covers: FIRE, SIP, asset allocation, insurance gap, emergency fund.
"""
from __future__ import annotations
import math
from typing import Optional


# ── Constants ────────────────────────────────────────────────────────────────
INDIA_INFLATION_RATE = 0.06          # 6% long-term inflation
EQUITY_RETURN = 0.12                 # 12% CAGR equity
DEBT_RETURN = 0.07                   # 7% debt/FD
SAFE_WITHDRAWAL_RATE = 0.035         # 3.5% SWR for India (conservative)
EMERGENCY_FUND_MONTHS = 6


# ── FIRE Calculations ─────────────────────────────────────────────────────────

def calculate_fire_number(monthly_expenses: float, inflation_years: int = 0) -> float:
    """FIRE corpus needed based on current monthly expenses."""
    annual_expenses = monthly_expenses * 12
    if inflation_years > 0:
        annual_expenses *= (1 + INDIA_INFLATION_RATE) ** inflation_years
    return round(annual_expenses / SAFE_WITHDRAWAL_RATE, 2)


def calculate_fire_with_target(
    age: int,
    annual_income: float,
    monthly_expenses: float,
    existing_corpus: float,
    target_retirement_age: int,
    target_monthly_draw: float,
    risk_profile: str = "moderate",
) -> dict:
    """
    Full FIRE calculation with custom retirement age and monthly draw target.
    Works for any inputs — not hardcoded to age 60.
    """
    years_to_retire = max(target_retirement_age - age, 1)

    # Inflate target monthly draw to retirement date
    inflated_monthly_draw = target_monthly_draw * (1 + INDIA_INFLATION_RATE) ** years_to_retire
    fire_number = (inflated_monthly_draw * 12) / SAFE_WITHDRAWAL_RATE

    monthly_savings = max((annual_income / 12) - monthly_expenses, 0)
    alloc = asset_allocation(age, risk_profile)
    equity_pct = alloc["equity_pct"] / 100
    blended_return = equity_pct * EQUITY_RETURN + (1 - equity_pct) * DEBT_RETURN

    # SIP needed to reach fire_number in years_to_retire
    sip_needed = calculate_sip_for_goal(
        fire_number, years_to_retire,
        annual_return=blended_return,
        existing_corpus=existing_corpus,
    )

    # Actual retirement date given current savings rate
    actual_years = calculate_years_to_fire(existing_corpus, monthly_savings, fire_number, blended_return)
    actual_retirement_age = round(age + actual_years, 1)

    # Corpus at target retirement age with current savings
    corpus_at_target = _future_value(existing_corpus, monthly_savings, years_to_retire, blended_return)

    return {
        "target_retirement_age": target_retirement_age,
        "target_monthly_draw_today": target_monthly_draw,
        "target_monthly_draw_at_retirement": round(inflated_monthly_draw, 0),
        "fire_number": round(fire_number, 0),
        "existing_corpus": existing_corpus,
        "years_to_target": years_to_retire,
        "monthly_sip_needed": round(sip_needed, 0),
        "current_monthly_savings": round(monthly_savings, 0),
        "sip_gap": round(max(sip_needed - monthly_savings, 0), 0),
        "corpus_at_target_with_current_savings": round(corpus_at_target, 0),
        "shortfall_at_target": round(max(fire_number - corpus_at_target, 0), 0),
        "actual_retirement_age_at_current_rate": actual_retirement_age,
        "on_track": corpus_at_target >= fire_number * 0.95,
        "asset_allocation": asset_allocation(age, risk_profile),
        "blended_return_assumed": round(blended_return * 100, 1),
    }


def _future_value(corpus: float, monthly_sip: float, years: int, annual_return: float) -> float:
    r = annual_return / 12
    n = years * 12
    return corpus * (1 + r) ** n + monthly_sip * (((1 + r) ** n - 1) / r)


def asset_allocation_glidepath(
    current_age: int,
    retirement_age: int,
    risk_profile: str = "moderate",
) -> list[dict]:
    """
    Year-by-year asset allocation glidepath from now to retirement.
    Equity reduces as retirement approaches — standard lifecycle investing.
    """
    glidepath = []
    for age in range(current_age, retirement_age + 1):
        alloc = asset_allocation(age, risk_profile)
        years_to_retire = retirement_age - age
        # Accelerate de-risking in last 5 years
        if years_to_retire <= 5:
            equity = max(alloc["equity_pct"] - (5 - years_to_retire) * 5, 20)
            debt = 100 - equity
        else:
            equity = alloc["equity_pct"]
            debt = alloc["debt_pct"]
        glidepath.append({
            "age": age,
            "years_to_retire": years_to_retire,
            "equity_pct": equity,
            "debt_pct": debt,
        })
    return glidepath


def sip_by_fund_category(
    total_monthly_sip: float,
    age: int,
    risk_profile: str = "moderate",
    years_to_retire: int = 20,
) -> list[dict]:
    """
    Break down total SIP into fund categories based on age and risk.
    Generic — works for any age/risk/horizon.
    """
    alloc = asset_allocation(age, risk_profile)
    equity_pct = alloc["equity_pct"] / 100
    debt_pct = alloc["debt_pct"] / 100

    equity_sip = total_monthly_sip * equity_pct
    debt_sip = total_monthly_sip * debt_pct

    categories = []

    if years_to_retire >= 10:
        # Long horizon: split equity into large-cap index + mid-cap
        categories += [
            {
                "category": "Large-cap Index Fund (Nifty 50 / Sensex)",
                "monthly_sip": round(equity_sip * 0.50, 0),
                "allocation_pct": round(equity_pct * 50, 1),
                "rationale": "Core equity — low cost, market returns, high liquidity",
                "risk": "Medium", "liquidity": "High (T+1)",
            },
            {
                "category": "Flexi-cap / Multi-cap Fund",
                "monthly_sip": round(equity_sip * 0.30, 0),
                "allocation_pct": round(equity_pct * 30, 1),
                "rationale": "Diversified across market caps for alpha",
                "risk": "Medium-High", "liquidity": "High (T+1)",
            },
            {
                "category": "Mid-cap Index Fund",
                "monthly_sip": round(equity_sip * 0.20, 0),
                "allocation_pct": round(equity_pct * 20, 1),
                "rationale": "Higher growth potential for long horizon",
                "risk": "High", "liquidity": "High (T+1)",
            },
        ]
    else:
        # Shorter horizon: conservative equity
        categories.append({
            "category": "Large-cap Index Fund",
            "monthly_sip": round(equity_sip, 0),
            "allocation_pct": round(equity_pct * 100, 1),
            "rationale": "Stable equity for medium horizon",
            "risk": "Medium", "liquidity": "High",
        })

    if debt_pct > 0:
        if years_to_retire >= 5:
            categories.append({
                "category": "PPF / EPF (Sec 80C eligible)",
                "monthly_sip": round(debt_sip * 0.60, 0),
                "allocation_pct": round(debt_pct * 60, 1),
                "rationale": "Tax-free, government-backed, ~7.1% p.a.",
                "risk": "Very Low", "liquidity": "Low (15yr lock-in)",
            })
            categories.append({
                "category": "Short-duration Debt Fund",
                "monthly_sip": round(debt_sip * 0.40, 0),
                "allocation_pct": round(debt_pct * 40, 1),
                "rationale": "Liquid debt allocation, better than FD post-tax",
                "risk": "Low", "liquidity": "High (T+1)",
            })
        else:
            categories.append({
                "category": "Liquid / Ultra Short-term Fund",
                "monthly_sip": round(debt_sip, 0),
                "allocation_pct": round(debt_pct * 100, 1),
                "rationale": "Capital preservation near retirement",
                "risk": "Very Low", "liquidity": "Very High",
            })

    return [c for c in categories if c["monthly_sip"] > 0]
    """FIRE corpus needed based on current monthly expenses."""
    annual_expenses = monthly_expenses * 12
    # Inflate expenses to retirement date
    if inflation_years > 0:
        annual_expenses *= (1 + INDIA_INFLATION_RATE) ** inflation_years
    return round(annual_expenses / SAFE_WITHDRAWAL_RATE, 2)


def calculate_years_to_fire(
    current_corpus: float,
    monthly_savings: float,
    fire_number: float,
    annual_return: float = EQUITY_RETURN,
) -> float:
    """Binary-search for years needed to reach FIRE number."""
    if current_corpus >= fire_number:
        return 0.0
    r = annual_return / 12  # monthly rate
    for months in range(1, 600):  # max 50 years
        fv = current_corpus * (1 + r) ** months + monthly_savings * (((1 + r) ** months - 1) / r)
        if fv >= fire_number:
            return round(months / 12, 1)
    return 50.0  # cap


def calculate_sip_for_goal(
    goal_amount: float,
    years: int,
    annual_return: float = EQUITY_RETURN,
    existing_corpus: float = 0.0,
) -> float:
    """Monthly SIP needed to reach a goal amount in given years."""
    n = years * 12
    r = annual_return / 12
    # Future value of existing corpus
    fv_existing = existing_corpus * (1 + r) ** n
    remaining = goal_amount - fv_existing
    if remaining <= 0:
        return 0.0
    sip = (remaining * r) / ((1 + r) ** n - 1)
    return round(max(sip, 0), 2)


def asset_allocation(age: int, risk_profile: str = "moderate") -> dict:
    """Age + risk adjusted asset allocation."""
    base_equity = max(100 - age, 20)
    adjustments = {"conservative": -15, "moderate": 0, "aggressive": +15}
    equity = min(max(base_equity + adjustments.get(risk_profile, 0), 10), 90)
    debt = 100 - equity
    return {
        "equity_pct": equity,
        "debt_pct": debt,
        "recommended": f"{equity}% Equity (Index funds/Large-cap) | {debt}% Debt (PPF/FD/Bonds)"
    }


def emergency_fund_target(monthly_expenses: float) -> float:
    return round(monthly_expenses * EMERGENCY_FUND_MONTHS, 2)


def insurance_gap_analysis(
    annual_income: float,
    existing_term_cover: float = 0.0,
    existing_health_cover: float = 0.0,
    dependents: int = 0,
) -> dict:
    """Rough insurance gap — IRDAI thumb rules."""
    recommended_term = annual_income * 10  # 10x income
    recommended_health = 500000 if dependents == 0 else 1000000  # 5L / 10L family
    term_gap = max(recommended_term - existing_term_cover, 0)
    health_gap = max(recommended_health - existing_health_cover, 0)
    return {
        "recommended_term_cover": recommended_term,
        "term_gap": term_gap,
        "recommended_health_cover": recommended_health,
        "health_gap": health_gap,
        "term_premium_estimate": round(term_gap * 0.0008, 0),   # ~₹800/lakh/year
        "health_premium_estimate": round(recommended_health * 0.005, 0),
    }


def corpus_growth_projection(
    current_corpus: float,
    monthly_sip: float,
    years: int,
    annual_return: float = EQUITY_RETURN,
) -> list[dict]:
    """Year-by-year corpus projection for charting."""
    r = annual_return / 12
    projection = []
    corpus = current_corpus
    for year in range(1, years + 1):
        corpus = corpus * (1 + r) ** 12 + monthly_sip * (((1 + r) ** 12 - 1) / r)
        projection.append({"year": year, "corpus": round(corpus, 0)})
    return projection


# ── Goal-based SIP Planner ────────────────────────────────────────────────────

COMMON_GOALS = {
    "emergency_fund":   {"label": "Emergency Fund",        "years": 1,  "priority": 1},
    "house":            {"label": "Down Payment for House", "years": 5,  "priority": 2},
    "child_education":  {"label": "Child's Education",      "years": 15, "priority": 3},
    "retirement":       {"label": "Retirement Corpus",      "years": 30, "priority": 4},
    "car":              {"label": "Car Purchase",           "years": 3,  "priority": 5},
    "vacation":         {"label": "International Vacation", "years": 2,  "priority": 6},
}


def plan_goals(
    goals: list[dict],
    monthly_investable: float,
    age: int,
    risk_profile: str = "moderate",
) -> dict:
    """
    Given a list of goals and investable surplus, allocate SIPs per goal.
    Returns per-goal SIP, total SIP needed, and whether it fits the budget.
    """
    alloc = asset_allocation(age, risk_profile)
    equity_return = EQUITY_RETURN
    debt_return = DEBT_RETURN

    planned = []
    total_sip_needed = 0.0

    for g in goals:
        years = g.get("target_years", 5)
        # Use equity return for long-term (>7yr), blended for medium, debt for short
        if years >= 7:
            rate = equity_return
            instrument = "Equity index funds / diversified mutual funds"
        elif years >= 3:
            rate = (equity_return + debt_return) / 2
            instrument = "Balanced / hybrid mutual funds"
        else:
            rate = debt_return
            instrument = "Liquid funds / FD / RD"

        sip = calculate_sip_for_goal(
            g.get("target_amount", 0),
            years,
            annual_return=rate,
            existing_corpus=g.get("existing_corpus", 0),
        )
        total_sip_needed += sip
        planned.append({
            "name": g.get("name", "Goal"),
            "target_amount": g.get("target_amount", 0),
            "target_years": years,
            "monthly_sip": round(sip, 0),
            "instrument": instrument,
            "return_assumed": round(rate * 100, 1),
            "feasible": sip <= monthly_investable * 0.4,  # single goal shouldn't eat >40%
        })

    return {
        "goals": planned,
        "total_sip_needed": round(total_sip_needed, 0),
        "monthly_investable": round(monthly_investable, 0),
        "surplus_after_sips": round(monthly_investable - total_sip_needed, 0),
        "all_goals_feasible": total_sip_needed <= monthly_investable,
    }


# ── Month-by-Month Roadmap ────────────────────────────────────────────────────

def generate_monthly_roadmap(
    annual_income: float,
    monthly_expenses: float,
    existing_corpus: float,
    age: int,
    tax_saving_gap: float = 0.0,
    emergency_fund_gap: float = 0.0,
    risk_profile: str = "moderate",
    scenario: str = "fire",
) -> list[dict]:
    """
    Generate a 12-month action roadmap.
    Each month has a specific action, target amount, and running corpus.
    """
    monthly_income = annual_income / 12
    monthly_surplus = monthly_income - monthly_expenses
    corpus = existing_corpus
    alloc = asset_allocation(age, risk_profile)
    equity_pct = alloc["equity_pct"] / 100
    r_monthly = EQUITY_RETURN / 12

    roadmap = []
    ef_remaining = emergency_fund_gap
    tax_remaining = tax_saving_gap

    for month in range(1, 13):
        actions = []
        invest_amount = 0.0

        # Month 1-2: Emergency fund first
        if ef_remaining > 0:
            ef_contribution = min(monthly_surplus * 0.5, ef_remaining)
            ef_remaining -= ef_contribution
            invest_amount += ef_contribution
            actions.append(f"Add ₹{ef_contribution:,.0f} to emergency fund (liquid fund/savings account)")

        # Month 1-3: Tax saving investments (if old regime)
        if tax_remaining > 0 and month <= 3:
            tax_contribution = min(monthly_surplus * 0.3, tax_remaining / 3)
            tax_remaining -= tax_contribution
            invest_amount += tax_contribution
            actions.append(f"Invest ₹{tax_contribution:,.0f} in tax-saving instruments (80C)")

        # Ongoing: SIP in equity
        sip_amount = round(monthly_surplus * equity_pct * 0.6, 0)
        invest_amount += sip_amount
        actions.append(f"SIP ₹{sip_amount:,.0f} in equity index funds")

        # Corpus grows
        corpus = corpus * (1 + r_monthly) + invest_amount

        roadmap.append({
            "month": month,
            "month_label": _month_label(month),
            "actions": actions,
            "invest_amount": round(invest_amount, 0),
            "running_corpus": round(corpus, 0),
            "focus": _month_focus(month, ef_remaining, tax_remaining),
        })

    return roadmap


def _month_label(month: int) -> str:
    from datetime import date, timedelta
    import calendar
    d = date.today().replace(day=1)
    for _ in range(month - 1):
        d = (d + timedelta(days=32)).replace(day=1)
    return d.strftime("%b %Y")


def _month_focus(month: int, ef_remaining: float, tax_remaining: float) -> str:
    if ef_remaining > 0: return "Emergency Fund"
    if tax_remaining > 0: return "Tax Saving"
    if month <= 6: return "Wealth Building"
    return "Goal SIPs"
