"""
Life Event Financial Calculator — pure deterministic logic.
Handles: bonus, inheritance, marriage, new baby, job change.
Each event returns a structured allocation plan + action checklist.
"""
from __future__ import annotations
from backend.tools.calculations import (
    calculate_sip_for_goal, emergency_fund_target,
    asset_allocation, calculate_fire_number
)
from backend.tools.tax_engine import (
    DeductionProfile, compare_regimes, _marginal_rate, STANDARD_DEDUCTION_OLD, LIMIT_80C
)

INDIA_INFLATION = 0.06


def handle_bonus(
    bonus_amount: float,
    annual_income: float,
    monthly_expenses: float,
    existing_corpus: float,
    age: int,
    risk_profile: str = "moderate",
    section_80c_invested: float = 0,
    section_80ccd1b: float = 0,
) -> dict:
    """Optimal allocation for a salary bonus."""
    # Tax on bonus (marginal rate)
    approx_taxable = max(annual_income - STANDARD_DEDUCTION_OLD - LIMIT_80C, 0)
    marginal = _marginal_rate(approx_taxable, "new")
    tax_on_bonus = round(bonus_amount * marginal * 1.04, 0)  # +4% cess
    post_tax_bonus = bonus_amount - tax_on_bonus

    # Emergency fund gap
    ef_target = emergency_fund_target(monthly_expenses)
    ef_current = existing_corpus * 0.10  # assume 10% in liquid
    ef_gap = max(ef_target - ef_current, 0)

    # 80C gap (tax saving opportunity)
    c80_gap = max(150_000 - section_80c_invested, 0)
    nps_gap = max(50_000 - section_80ccd1b, 0)
    tax_saving_opportunity = min(c80_gap + nps_gap, post_tax_bonus * 0.30)

    # Remaining for investment
    remaining = post_tax_bonus - min(ef_gap, post_tax_bonus * 0.20) - tax_saving_opportunity
    alloc = asset_allocation(age, risk_profile)
    equity_pct = alloc["equity_pct"] / 100

    allocation = {
        "emergency_fund_topup": round(min(ef_gap, post_tax_bonus * 0.20), 0),
        "tax_saving_80c_nps": round(tax_saving_opportunity, 0),
        "equity_investment": round(max(remaining * equity_pct, 0), 0),
        "debt_investment": round(max(remaining * (1 - equity_pct), 0), 0),
    }

    checklist = [
        f"Top up emergency fund to ₹{ef_target:,.0f} (6 months expenses) — put in liquid fund",
        f"Invest ₹{tax_saving_opportunity:,.0f} in 80C/NPS to save ₹{round(tax_saving_opportunity * marginal, 0):,.0f} in tax",
        f"SIP ₹{allocation['equity_investment']:,.0f} in equity index funds for long-term wealth",
        "Update your Will/nominee details if this significantly changes your net worth",
        "Do NOT spend bonus on lifestyle upgrades — let it compound for 5+ years",
    ]

    return {
        "event": "bonus",
        "gross_bonus": bonus_amount,
        "tax_on_bonus": tax_on_bonus,
        "post_tax_bonus": post_tax_bonus,
        "marginal_rate_pct": round(marginal * 100, 1),
        "allocation": allocation,
        "allocation_pct": {
            "emergency_fund": round(allocation["emergency_fund_topup"] / post_tax_bonus * 100, 1),
            "tax_saving": round(allocation["tax_saving_80c_nps"] / post_tax_bonus * 100, 1),
            "equity": round(allocation["equity_investment"] / post_tax_bonus * 100, 1),
            "debt": round(allocation["debt_investment"] / post_tax_bonus * 100, 1),
        },
        "checklist": checklist,
        "insight": "Bonus is taxed at your marginal rate — investing in 80C/NPS before year-end reduces the tax bite significantly.",
    }


def handle_inheritance(
    inheritance_amount: float,
    annual_income: float,
    monthly_expenses: float,
    existing_corpus: float,
    age: int,
    risk_profile: str = "moderate",
    has_home_loan: bool = False,
    home_loan_outstanding: float = 0,
) -> dict:
    """Optimal allocation for an inheritance windfall."""
    # Inheritance is NOT taxable in India (no inheritance tax)
    # But income from inherited assets IS taxable

    ef_target = emergency_fund_target(monthly_expenses)
    ef_gap = max(ef_target - existing_corpus * 0.10, 0)

    # Prepay home loan? Only if interest rate > 8.5%
    loan_prepay = 0
    if has_home_loan and home_loan_outstanding > 0:
        loan_prepay = min(home_loan_outstanding * 0.30, inheritance_amount * 0.25)

    remaining = inheritance_amount - min(ef_gap, inheritance_amount * 0.15) - loan_prepay
    alloc = asset_allocation(age, risk_profile)
    equity_pct = alloc["equity_pct"] / 100

    # For large amounts, stagger equity investment (STP over 6-12 months)
    stagger = inheritance_amount > 2_000_000

    allocation = {
        "emergency_fund_topup": round(min(ef_gap, inheritance_amount * 0.15), 0),
        "home_loan_prepayment": round(loan_prepay, 0),
        "equity_investment": round(remaining * equity_pct, 0),
        "debt_investment": round(remaining * (1 - equity_pct), 0),
    }

    checklist = [
        "Inheritance is NOT taxable in India — no inheritance tax exists",
        "Income earned FROM inherited assets (rent, dividends) IS taxable in your hands",
        f"Build/top up emergency fund to ₹{ef_target:,.0f} first",
        f"{'Prepay 30% of home loan to reduce interest burden' if has_home_loan else 'Consider term insurance if you have dependents'}",
        f"{'Invest via STP (Systematic Transfer Plan) over 6-12 months — avoid lump sum in equity' if stagger else 'Invest in equity index funds for long-term growth'}",
        "Update your Will to include inherited assets",
        "Consult a CA if inherited property — capital gains tax applies on future sale",
    ]

    return {
        "event": "inheritance",
        "amount": inheritance_amount,
        "tax_note": "Inheritance itself is NOT taxable in India. Income from inherited assets is taxable.",
        "allocation": allocation,
        "stagger_investment": stagger,
        "stagger_note": "Amount > ₹20L — consider STP over 6-12 months to avoid timing risk" if stagger else None,
        "checklist": checklist,
        "insight": "India has no inheritance tax. However, if you inherit property and sell it later, capital gains tax applies based on the original owner's purchase price.",
    }


def handle_marriage(
    your_income: float,
    partner_income: float,
    your_corpus: float,
    partner_corpus: float,
    monthly_expenses_combined: float,
    your_age: int,
    risk_profile: str = "moderate",
    planning_home: bool = False,
    planning_child: bool = False,
) -> dict:
    """Financial plan for marriage — joint finances, goals, insurance."""
    combined_income = your_income + partner_income
    combined_corpus = your_corpus + partner_corpus
    ef_target = emergency_fund_target(monthly_expenses_combined)
    monthly_surplus = max(combined_income / 12 - monthly_expenses_combined, 0)

    # Home down payment goal (if planning)
    home_sip = 0
    if planning_home:
        home_corpus_target = 2_000_000  # ₹20L down payment
        home_sip = calculate_sip_for_goal(home_corpus_target, 3)

    # Child planning
    child_sip = 0
    if planning_child:
        child_education = 2_500_000  # ₹25L in 18 years
        child_sip = calculate_sip_for_goal(child_education, 18)

    # Recommended term cover (10x combined income)
    recommended_term = combined_income * 10
    recommended_health = 1_000_000  # ₹10L family floater

    checklist = [
        f"Open a joint savings account for household expenses — target ₹{monthly_expenses_combined:,.0f}/month",
        f"Build combined emergency fund of ₹{ef_target:,.0f} (6 months combined expenses)",
        f"Get a family floater health insurance of ₹{recommended_health/100000:.0f}L — cheaper than two individual policies",
        f"Both partners should have term insurance of ₹{recommended_term/100000:.0f}L each (10x income)",
        "Update nominees on all investments, insurance, and bank accounts",
        "Maintain separate investment accounts — joint finances ≠ merged investments",
        f"{'Start SIP of ₹' + f'{home_sip:,.0f}' + '/month for home down payment (3-year goal)' if planning_home else 'Discuss home purchase timeline and start saving for down payment'}",
        f"{'Start child education SIP of ₹' + f'{child_sip:,.0f}' + '/month (₹25L in 18 years)' if planning_child else 'Discuss family planning timeline'}",
        "File taxes separately — both partners can claim 80C, 80D independently",
    ]

    return {
        "event": "marriage",
        "combined_income": combined_income,
        "combined_corpus": combined_corpus,
        "monthly_surplus": round(monthly_surplus, 0),
        "emergency_fund_target": ef_target,
        "recommended_term_cover_each": recommended_term,
        "recommended_health_cover": recommended_health,
        "goal_sips": {
            "home_down_payment": home_sip if planning_home else None,
            "child_education": child_sip if planning_child else None,
        },
        "checklist": checklist,
        "insight": "In India, both spouses can independently claim 80C (₹1.5L each) and 80D deductions — that's ₹3L+ in combined 80C savings.",
    }


def handle_new_baby(
    annual_income: float,
    monthly_expenses: float,
    existing_corpus: float,
    age: int,
    risk_profile: str = "moderate",
    is_girl: bool = False,
) -> dict:
    """Financial plan for a new baby — education corpus, insurance, SSY."""
    # Education corpus targets (inflation-adjusted 18 years)
    graduation_cost_today = 2_000_000   # ₹20L today
    graduation_inflated = graduation_cost_today * (1 + INDIA_INFLATION) ** 18
    graduation_sip = calculate_sip_for_goal(graduation_inflated, 18)

    pg_cost_today = 3_000_000  # ₹30L for PG/MBA today
    pg_inflated = pg_cost_today * (1 + INDIA_INFLATION) ** 22
    pg_sip = calculate_sip_for_goal(pg_inflated, 22)

    # Sukanya Samriddhi Yojana (SSY) — only for girls
    ssy_annual_max = 150_000
    ssy_note = "SSY: Invest up to ₹1.5L/year, matures at 21 years, ~8.2% p.a., EEE tax status" if is_girl else None

    # Updated insurance needs
    new_term_cover = annual_income * 15  # increase to 15x with child
    new_health_cover = 1_000_000  # ₹10L family floater

    # Monthly budget impact
    baby_monthly_cost = round(monthly_expenses * 0.20, 0)  # ~20% increase

    checklist = [
        f"Start education SIP of ₹{graduation_sip:,.0f}/month for graduation corpus (₹{graduation_inflated/100000:.0f}L in 18 years)",
        f"{'Open Sukanya Samriddhi Yojana account — invest up to ₹1.5L/year, ~8.2% p.a., EEE tax status' if is_girl else 'Consider ELSS SIP for child education — 3-year lock-in, equity returns'}",
        f"Increase term insurance to ₹{new_term_cover/100000:.0f}L (15x income with child dependent)",
        f"Upgrade health insurance to ₹{new_health_cover/100000:.0f}L family floater",
        f"Budget ₹{baby_monthly_cost:,.0f}/month extra for baby expenses (20% of current expenses)",
        "Write a Will — critical when you have a minor dependent",
        "Nominate child as beneficiary in all investments and insurance",
        "Start PPF account in child's name — ₹500/year minimum, 15-year lock-in",
    ]

    return {
        "event": "new_baby",
        "is_girl": is_girl,
        "education_goals": {
            "graduation": {
                "target_today": graduation_cost_today,
                "target_inflated_18yr": round(graduation_inflated, 0),
                "monthly_sip": round(graduation_sip, 0),
                "instrument": "Equity index fund / ELSS",
            },
            "pg_mba": {
                "target_today": pg_cost_today,
                "target_inflated_22yr": round(pg_inflated, 0),
                "monthly_sip": round(pg_sip, 0),
                "instrument": "Equity index fund",
            },
        },
        "ssy": {"applicable": is_girl, "note": ssy_note, "annual_max": ssy_annual_max if is_girl else None},
        "insurance_update": {
            "term_cover_recommended": new_term_cover,
            "health_cover_recommended": new_health_cover,
        },
        "monthly_budget_increase": baby_monthly_cost,
        "checklist": checklist,
        "insight": f"{'Sukanya Samriddhi Yojana (SSY) is the best instrument for a girl child — government-backed, ~8.2% p.a., fully tax-free (EEE status), and counts towards 80C.' if is_girl else 'Starting a ₹5,000/month SIP at birth grows to ₹50L+ by age 18 at 12% CAGR — time is your biggest asset.'}",
    }


def handle_job_change(
    old_income: float,
    new_income: float,
    joining_bonus: float,
    pf_corpus: float,
    age: int,
    monthly_expenses: float,
    risk_profile: str = "moderate",
) -> dict:
    """Financial decisions around a job change."""
    income_increase = new_income - old_income
    income_increase_pct = round((income_increase / old_income) * 100, 1) if old_income else 0

    # PF transfer vs withdrawal
    pf_tax_if_withdrawn = pf_corpus * 0.10 if age < 58 else 0  # 10% TDS if < 5 yrs service
    pf_recommendation = "transfer" if age < 50 else "keep_in_epfo"

    # Lifestyle inflation trap
    safe_lifestyle_increase = income_increase * 0.30  # max 30% of raise on lifestyle
    invest_from_raise = income_increase / 12 * 0.70  # invest 70% of monthly raise

    checklist = [
        f"Transfer PF to new employer — do NOT withdraw (₹{pf_corpus:,.0f} will lose ₹{pf_tax_if_withdrawn:,.0f} in TDS + miss compounding)",
        f"Income increased by {income_increase_pct}% — invest ₹{invest_from_raise:,.0f}/month of the raise, not just lifestyle",
        f"{'Invest joining bonus of ₹' + f'{joining_bonus:,.0f}' + ' — see bonus allocation plan' if joining_bonus > 0 else 'Negotiate joining bonus if not offered'}",
        "Review and update health insurance — new employer may have different coverage",
        "Check ESOP/RSU vesting schedule at old employer before resigning",
        "Serve full notice period — avoid salary recovery clauses",
        "Update IT returns with both Form 16s (old + new employer) for the year",
        "Renegotiate salary structure — higher HRA, NPS contribution reduces tax",
    ]

    return {
        "event": "job_change",
        "old_income": old_income,
        "new_income": new_income,
        "income_increase": income_increase,
        "income_increase_pct": income_increase_pct,
        "pf_corpus": pf_corpus,
        "pf_recommendation": pf_recommendation,
        "pf_tax_if_withdrawn": pf_tax_if_withdrawn,
        "monthly_invest_from_raise": round(invest_from_raise, 0),
        "safe_lifestyle_increase_monthly": round(safe_lifestyle_increase / 12, 0),
        "checklist": checklist,
        "insight": "The biggest wealth-building mistake after a raise is 'lifestyle inflation' — spending 100% of the increase. Invest 70% of every raise and you'll retire 10 years earlier.",
    }
