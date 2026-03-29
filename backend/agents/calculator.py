"""
Calculator Agent — pure deterministic math, zero LLM.
Runs all calculations based on complete user profile.
"""
from __future__ import annotations
from backend.models.schemas import AgentState
from backend.tools.calculations import (
    calculate_fire_number,
    calculate_fire_with_target,
    calculate_years_to_fire,
    calculate_sip_for_goal,
    asset_allocation,
    asset_allocation_glidepath,
    sip_by_fund_category,
    emergency_fund_target,
    insurance_gap_analysis,
    corpus_growth_projection,
    plan_goals,
    generate_monthly_roadmap,
)
from backend.tools.tax_engine import (
    DeductionProfile,
    compare_regimes,
    identify_missed_deductions,
    calculate_tax,
    calculate_tax_with_steps,
    calculate_hra_exemption,
    tax_saving_instruments,
)
from backend.tools.literacy_score import compute_literacy_score


def run_calculator(state: AgentState) -> AgentState:
    """Run all relevant calculations based on scenario."""
    p = state.profile
    results = {}

    try:
        # ── HRA exemption (compute before tax if HRA received) ────────────────
        if p.hra_received > 0 and p.annual_income:
            # Estimate basic as 40% of CTC (common structure)
            estimated_basic = p.annual_income * 0.40
            # Estimate rent as HRA received (conservative — user may not have given rent)
            rent_paid = p.hra_received * 1.2  # assume rent slightly > HRA
            hra_calc = calculate_hra_exemption(
                annual_hra_received=p.hra_received,
                annual_basic=estimated_basic,
                annual_rent_paid=rent_paid,
                metro_city=True,
            )
            results["hra_calculation"] = hra_calc
            # Use computed exemption
            hra_exempt = hra_calc["hra_exempt"]
        else:
            hra_exempt = p.hra_exempt

        # ── Tax calculations ──────────────────────────────────────────────────
        if p.annual_income:
            deductions = DeductionProfile(
                section_80c=p.section_80c_invested,
                section_80d_self=p.section_80d_self,
                section_80d_parents=p.section_80d_parents,
                section_80ccd1b=p.section_80ccd1b,
                hra_exempt=hra_exempt,
                lta=p.lta,
                home_loan_interest=p.home_loan_interest,
                age=p.age or 30,
            )
            results["tax_comparison"] = compare_regimes(p.annual_income, deductions)
            results["missed_deductions"] = identify_missed_deductions(p.annual_income, deductions)

            # Step-by-step trace for both regimes (judge requirement)
            rec = results["tax_comparison"]["recommended_regime"]
            results["tax_steps_new"] = calculate_tax_with_steps(p.annual_income, deductions, "new")
            results["tax_steps_old"] = calculate_tax_with_steps(p.annual_income, deductions, "old")

            # Tax-saving instruments ranked by liquidity + risk
            results["tax_instruments"] = tax_saving_instruments(p.annual_income, deductions, rec)

            if p.spouse_income:
                results["spouse_tax"] = calculate_tax(p.spouse_income, DeductionProfile(), "new")
                results["combined_income"] = p.annual_income + p.spouse_income

        # ── FIRE calculations — only for fire/life_event scenarios ─────────
        if state.scenario in ("fire", "life_event") and p.annual_income and p.monthly_expenses and p.age:
            current_corpus = (p.existing_corpus or 0.0) + p.existing_mf + p.existing_ppf
            monthly_savings = max((p.annual_income / 12) - p.monthly_expenses, 0)

            # Use custom retirement age if specified, else default 60
            retirement_age = p.target_retirement_age or 60
            years_to_retirement = max(retirement_age - p.age, 1)

            if p.target_monthly_draw:
                # Full FIRE with target draw — judge scenario 1
                fire_result = calculate_fire_with_target(
                    age=p.age,
                    annual_income=p.annual_income,
                    monthly_expenses=p.monthly_expenses,
                    existing_corpus=current_corpus,
                    target_retirement_age=retirement_age,
                    target_monthly_draw=p.target_monthly_draw,
                    risk_profile=p.risk_profile,
                )
                results["fire"] = fire_result
                fire_number = fire_result["fire_number"]
                sip_needed = fire_result["monthly_sip_needed"]
            else:
                # Standard FIRE
                fire_number = calculate_fire_number(p.monthly_expenses, years_to_retirement)
                years_to_fire = calculate_years_to_fire(current_corpus, monthly_savings, fire_number)
                sip_needed = calculate_sip_for_goal(fire_number, years_to_retirement, existing_corpus=current_corpus)
                ef_target = emergency_fund_target(p.monthly_expenses)
                results["fire"] = {
                    "fire_number": fire_number,
                    "current_corpus": current_corpus,
                    "monthly_savings_available": round(monthly_savings, 2),
                    "years_to_fire": years_to_fire,
                    "fire_age": round(p.age + years_to_fire, 1),
                    "target_retirement_age": retirement_age,
                    "monthly_sip_needed": round(sip_needed, 0),
                    "emergency_fund_target": ef_target,
                    "emergency_fund_gap": round(max(ef_target - current_corpus * 0.1, 0), 0),
                    "asset_allocation": asset_allocation(p.age, p.risk_profile),
                    "corpus_projection": corpus_growth_projection(current_corpus, monthly_savings * 0.7, min(years_to_retirement, 30)),
                }

            # Asset allocation glidepath (year-by-year)
            results["glidepath"] = asset_allocation_glidepath(p.age, retirement_age, p.risk_profile)

            # SIP by fund category
            results["sip_by_category"] = sip_by_fund_category(
                total_monthly_sip=sip_needed,
                age=p.age,
                risk_profile=p.risk_profile,
                years_to_retire=years_to_retirement,
            )

            # Goal plan
            ef_gap = results["fire"].get("emergency_fund_gap", 0)
            goals_input = [g.model_dump() for g in p.goals] if p.goals else [
                {"name": "Emergency Fund", "target_amount": emergency_fund_target(p.monthly_expenses), "target_years": 1, "existing_corpus": 0},
                {"name": f"Retirement at {retirement_age}", "target_amount": fire_number, "target_years": years_to_retirement, "existing_corpus": current_corpus},
            ]
            results["goal_plan"] = plan_goals(goals_input, monthly_savings, p.age, p.risk_profile)

            # Month-by-month roadmap
            tax_gap = sum(d.get("gap", 0) for d in results.get("missed_deductions", []))
            results["monthly_roadmap"] = generate_monthly_roadmap(
                annual_income=p.annual_income,
                monthly_expenses=p.monthly_expenses,
                existing_corpus=current_corpus,
                age=p.age,
                tax_saving_gap=tax_gap,
                emergency_fund_gap=ef_gap,
                risk_profile=p.risk_profile,
                scenario=state.scenario,
            )

        # ── Insurance gap ─────────────────────────────────────────────────────
        if state.scenario in ("fire", "life_event") and p.annual_income:
            results["insurance"] = insurance_gap_analysis(
                p.annual_income, p.term_cover, p.health_cover, p.dependents
            )

        # ── Life event ────────────────────────────────────────────────────────
        if p.life_event and p.life_event_amount:
            results["life_event"] = _handle_life_event(p, results)

        # ── Literacy score ────────────────────────────────────────────────────
        results["literacy_score"] = compute_literacy_score(p, state.messages)

        state.calculation_results = results

    except Exception as e:
        state.error = f"Calculation error: {str(e)}"

    return state


def _handle_life_event(p, existing_results: dict) -> dict:
    """Calculate optimal allocation for life event windfall/change."""
    amount = p.life_event or 0
    event = p.life_event
    result = {"event": event, "amount": p.life_event_amount}

    if event in ("bonus", "inheritance") and p.life_event_amount:
        windfall = p.life_event_amount
        emergency_gap = 0
        if p.monthly_expenses:
            target_ef = emergency_fund_target(p.monthly_expenses)
            current_ef = (p.existing_corpus or 0) * 0.1  # assume 10% in liquid
            emergency_gap = max(target_ef - current_ef, 0)

        tax_saving_gap = sum(
            d.get("gap", 0) for d in existing_results.get("missed_deductions", [])
        )

        result["recommended_allocation"] = {
            "emergency_fund_topup": min(emergency_gap, windfall * 0.2),
            "tax_saving_investments": min(tax_saving_gap, windfall * 0.3),
            "equity_investment": round(windfall * 0.4, 2),
            "debt_investment": round(windfall * 0.1, 2),
        }

    elif event == "marriage":
        result["advice_points"] = [
            "Combine emergency funds — target 6 months of combined expenses",
            "Review and update nominees on all policies and investments",
            "Evaluate joint home loan eligibility — higher combined income helps",
            "Maintain separate investment accounts for individual goals",
            "Review health insurance — family floater may be more cost-effective",
        ]

    elif event == "baby":
        child_education_corpus = 2_500_000  # ₹25L for graduation in 18 years
        sip_for_child = calculate_sip_for_goal(child_education_corpus, 18)
        result["child_planning"] = {
            "education_corpus_target": child_education_corpus,
            "monthly_sip_for_education": sip_for_child,
            "recommended_instruments": ["Sukanya Samriddhi (if girl)", "ELSS", "Index Fund"],
        }

    return result
