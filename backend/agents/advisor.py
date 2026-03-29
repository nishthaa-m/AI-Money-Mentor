"""
Advisor Agent — interprets calculated numbers into plain, actionable advice.
Uses GPT-4o (expensive model). Only runs after calculations are complete.
Produces specific, personalised plan — no raw numbers dumped on user.
"""
import os
import re
import json
from functools import lru_cache
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

from backend.models.schemas import AgentState


@lru_cache(maxsize=1)
def get_big_model():
    key = os.getenv("OPENROUTER_API_KEY")
    if not key or key == "your_openrouter_api_key_here":
        raise RuntimeError("OPENROUTER_API_KEY not set in .env")
    return ChatOpenAI(
        model="google/gemini-2.0-flash-001",  # fast, cheap, excellent at structured JSON
        temperature=0.4,
        base_url="https://openrouter.ai/api/v1",
        api_key=key,
        default_headers={
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "AI Money Mentor",
        },
    )

ADVISOR_SYSTEM = """You are a sharp, warm Indian financial mentor on Economic Times. You speak like a knowledgeable friend who is also a CA — direct, clear, uses Indian context naturally.

Return ONLY a valid JSON object. No explanation, no markdown. Just the JSON.

IMPORTANT ACCURACY RULES (India FY 2025-26 — Finance Act 2025):
- New regime standard deduction: ₹75,000
- New regime ZERO TAX up to ₹12.75L gross income (₹12L taxable after std ded) — rebate u/s 87A
- New regime slabs: 0-4L=0%, 4-8L=5%, 8-12L=10%, 12-16L=15%, 16-20L=20%, 20-24L=25%, above 24L=30%
- Old regime slabs: 0-2.5L=0%, 2.5-5L=5%, 5-10L=20%, above 10L=30% (std ded ₹50k)
- Old regime rebate 87A: zero tax if taxable ≤ ₹5L
- Sec 80C limit: ₹1,50,000 (ELSS, PPF, NSC, LIC, 5yr FD, home loan principal)
- Sec 80CCD(1B): additional ₹50,000 for NPS Tier-1 (OVER and ABOVE 80C — total ₹2L possible)
- Sec 80D: ₹25,000 self+family; ₹50,000 if senior citizen; same limits for parents
- Sec 24(b): home loan interest ₹2,00,000 (self-occupied property)
- Deductions (80C, 80D, 80CCD etc.) are NOT available under new regime
- 4% Health & Education Cess on all tax
- Surcharge: 10% if taxable > 50L, 15% if > 1Cr, 25% if > 2Cr, 37% if > 5Cr

SEBI COMPLIANCE:
- Never name specific mutual fund schemes or stocks
- Say "tax-saving mutual funds (ELSS category)" not "invest in XYZ fund"
- Say "consider" or "you may want to" — never "you must" or "guaranteed"
- All tax figures must match the calculation results provided — never invent numbers

JSON Schema:
{
  "headline": "One punchy sentence — biggest win with exact ₹ amount from calculations",
  "tone_opener": "1-2 warm sentences acknowledging their specific situation (age, income, scenario)",
  "tax": {
    "recommended_regime": "new or old",
    "annual_saving": <from calculations>,
    "monthly_saving": <annual_saving / 12>,
    "their_tax": <total tax under recommended regime>,
    "effective_rate": <effective rate % under recommended regime>,
    "monthly_tds": <their_tax / 12>,
    "regime_reason": "One sentence: WHY this regime is better — mention the specific ₹ difference",
    "step_by_step": "3-4 sentence plain-English walkthrough of the tax calculation — e.g. 'Your gross income is ₹18L. After standard deduction of ₹75K, taxable income is ₹17.25L. Tax on this under new regime slabs = ₹X. After 4% cess = ₹Y total.' Must be verifiable against the steps in tax_steps_new/old."
  },
  "deductions": [
    {
      "section": "80C",
      "what": "Tax-saving investments (ELSS, PPF, NSC, LIC)",
      "gap": <amount not yet invested>,
      "saving": <tax saving at marginal rate>,
      "how": "Specific step — e.g. Consider a monthly SIP of ₹X in tax-saving mutual funds (ELSS category)"
    }
  ],
  "fire": {
    "corpus_needed": <from calculations>,
    "retire_at_age": <target_retirement_age from calculations>,
    "actual_retire_age": <actual_retirement_age_at_current_rate — may differ from target>,
    "on_track": <true/false>,
    "monthly_sip_needed": <from calculations>,
    "current_monthly_savings": <from calculations>,
    "emergency_fund_gap": <from calculations>,
    "allocation": "e.g. 70% equity index funds, 30% debt (PPF/FD/bonds) — based on age X",
    "glidepath_summary": "1 sentence: how allocation shifts over time, e.g. 'Equity reduces from 66% now to 40% by age 50 as you approach retirement'"
  },
  "actions": [
    {"priority": 1, "action": "Specific actionable step with ₹ amount", "impact": "Saves/builds ₹X", "timeline": "This month"}
  ],
  "insight": "One genuinely useful India-specific insight they probably didn't know. Conversational, not textbook.",
  "life_event_advice": "For life_event scenario: a detailed 3-4 sentence string covering what to do financially for this specific event (marriage/bonus/baby/inheritance). Must be a plain string, NOT an object. For other scenarios: null"
}

Rules:
- deductions array: ONLY include if old regime is recommended (deductions don't apply in new regime)
- fire object: ONLY include if scenario is fire or life_event
- All ₹ amounts must come from the calculation results — never invent
- actions: max 3, ordered by ₹ impact, each must reference a specific number
- insight: something like "Most salaried Indians don't know that NPS gives you an extra ₹50,000 deduction over and above your 80C limit" — practical, India-specific
- Return ONLY the JSON, nothing else"""


def run_advisor(state: AgentState) -> AgentState:
    """Generate personalised advice from calculation results."""
    p = state.profile
    results = state.calculation_results
    scenario = state.scenario
    context = _build_context(p, results, scenario)
    messages = [SystemMessage(content=ADVISOR_SYSTEM), HumanMessage(content=context)]

    try:
        response = get_big_model().invoke(messages)
        raw = response.content.strip()

        # Strip markdown fences if model wraps in ```json
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

        # Validate it's parseable JSON — store in calculation_results for frontend
        try:
            parsed = json.loads(raw)
            state.calculation_results["advisor_plan"] = parsed
            state.advice_text = raw  # store raw JSON
        except json.JSONDecodeError:
            # Fallback: store as plain text
            state.advice_text = raw

        state.messages.append({"role": "assistant", "content": raw})

    except Exception as e:
        state.error = f"Advisor error: {str(e)}"
        state.advice_text = "I encountered an issue generating your plan. Please try again."

    return state


def _build_context(p, results: dict, scenario: str) -> str:
    name = p.name or "the user"
    life_event_str = f"\nLIFE EVENT: {p.life_event}" if p.life_event else ""
    scenario_instruction = {
        "tax": "Focus ONLY on tax optimisation. Do NOT include fire or retirement sections.",
        "fire": "Focus on retirement planning and FIRE. Include tax only as a supporting point.",
        "life_event": f"This is a LIFE EVENT scenario ({p.life_event or 'marriage/major event'}). Focus the entire plan on this life event — what to do financially before, during, and after. Include tax implications of the event. Do NOT give a generic retirement plan. The life_event_advice field must be a detailed string about this specific event.",
    }.get(scenario, "Provide a balanced financial plan.")

    lines = [
        f"SCENARIO: {scenario}",
        f"INSTRUCTION: {scenario_instruction}",
        f"User: {name}, Age: {p.age}, Annual Income: ₹{p.annual_income:,.0f}" if p.annual_income else f"User: {name}, Age: {p.age}",
        f"Monthly Expenses: ₹{p.monthly_expenses:,.0f}" if p.monthly_expenses else "",
        f"Risk Profile: {p.risk_profile} | Dependents: {p.dependents}",
        life_event_str,
        "",
        "=== CALCULATION RESULTS ===",
        json.dumps(results, indent=2, default=str),
        "",
        "Generate the personalised plan JSON based on these exact numbers and the scenario instruction above.",
    ]
    return "\n".join(l for l in lines if l is not None)
