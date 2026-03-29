"""
Orchestrator — LangGraph multi-agent graph.
Routes: Profiler → Calculator → Advisor → Compliance
"""
from __future__ import annotations
import os
import asyncio
from typing import Literal, Any
from functools import lru_cache

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from backend.models.schemas import AgentState, UserProfile
from backend.tools.compliance import apply_guardrail, validate_input_safety

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_HEADERS = {"HTTP-Referer": "http://localhost:3000", "X-Title": "AI Money Mentor"}

MAX_ITERATIONS = 10


def _get_api_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key or key == "your_openrouter_api_key_here":
        raise RuntimeError("OPENROUTER_API_KEY not set in .env")
    return key


@lru_cache(maxsize=1)
def get_small_model():
    return ChatOpenAI(
        model="meta-llama/llama-3.1-8b-instruct",
        temperature=0.2,
        base_url=OPENROUTER_BASE,
        api_key=_get_api_key(),
        default_headers=OPENROUTER_HEADERS,
    )


@lru_cache(maxsize=1)
def get_big_model():
    return ChatOpenAI(
        model="anthropic/claude-3.5-sonnet",
        temperature=0.3,
        base_url=OPENROUTER_BASE,
        api_key=_get_api_key(),
        default_headers=OPENROUTER_HEADERS,
    )


def _detect_scenario(state: AgentState) -> str:
    last_msg = state.messages[-1]["content"] if state.messages else ""
    prompt = f"""Classify this user message into exactly one category.

Categories:
- tax: user mentions salary, income, tax, Form 16, deductions, 80C, old/new regime, TDS, ITR, tax saving
- fire: user explicitly mentions retirement, FIRE, "retire early", SIP planning, investment roadmap, corpus
- life_event: user mentions a specific life event — bonus, marriage, baby/child, inheritance, job change
- unknown: none of the above clearly apply

Rules:
- If user only mentions salary/income and tax → "tax"
- If user mentions both tax AND retirement → "fire"  
- When in doubt → "tax" (most common query)

Message: "{last_msg}"

Reply with ONLY one word: tax / fire / life_event / unknown"""
    result = get_small_model().invoke([HumanMessage(content=prompt)])
    scenario = result.content.strip().lower().split()[0]
    return scenario if scenario in ("tax", "fire", "life_event") else "tax"


async def process_message(
    session_id: str,
    user_message: str,
    existing_state: dict | None = None,
) -> AgentState:
    """
    Main pipeline — runs synchronous agents in thread pool to avoid blocking.
    Flow: detect → profiler → calculator → advisor → compliance

    On follow-up messages after a plan has been delivered:
    - If user asks a clarifying question → answer conversationally
    - If user provides new data → re-run full pipeline with updated profile
    """
    if existing_state:
        state = AgentState(**existing_state)
    else:
        state = AgentState(session_id=session_id)

    state.messages.append({"role": "user", "content": user_message})
    state.iteration_count += 1
    state.is_complete = False

    # Input safety check
    valid, err = validate_input_safety(user_message)
    if not valid:
        state.messages.append({"role": "assistant", "content": err})
        state.is_complete = True
        return state

    loop = asyncio.get_event_loop()

    # ── Follow-up handling ────────────────────────────────────────────────────
    # If we already delivered a plan, check if this is a clarifying question
    # vs new data that should trigger a re-calculation
    already_has_plan = bool(state.calculation_results.get("advisor_plan"))
    if already_has_plan:
        intent = await loop.run_in_executor(None, _classify_followup, user_message)
        if intent == "question":
            # Answer conversationally using the existing plan as context
            state = await loop.run_in_executor(None, _answer_followup, state, user_message)
            return state
        # else: new data / wants recalculation — fall through to full pipeline

    # ── Full pipeline ─────────────────────────────────────────────────────────
    # Step 1: detect scenario
    if not state.scenario or state.scenario == "unknown":
        state.scenario = await loop.run_in_executor(None, _detect_scenario, state)

    # Step 2: profiler
    from backend.agents.profiler import run_profiler
    state = await loop.run_in_executor(None, run_profiler, state)
    if state.missing_fields:
        return state

    # Step 3: calculator
    from backend.agents.calculator import run_calculator
    state = run_calculator(state)
    if state.error:
        state.messages.append({"role": "assistant", "content": f"Calculation error: {state.error}"})
        return state

    # Step 4: advisor
    from backend.agents.advisor import run_advisor
    state = await loop.run_in_executor(None, run_advisor, state)

    # Step 5: compliance — audit log, language softening (no disclaimer appended to JSON)
    from backend.tools.compliance import _log_interaction, SOFTENING_RULES
    import re
    if state.advice_text:
        softened = state.advice_text
        for pattern, replacement in SOFTENING_RULES:
            softened = re.sub(pattern, replacement, softened, flags=re.IGNORECASE)
        state.advice_text = softened
        _log_interaction(state.user_id, state.scenario or "general", len(softened))
        for i in range(len(state.messages) - 1, -1, -1):
            if state.messages[i]["role"] == "assistant":
                state.messages[i]["content"] = softened
                break

    state.is_complete = True
    return state


def _classify_followup(user_message: str) -> str:
    """Classify whether a follow-up is a question or new data."""
    prompt = f"""A user has already received a financial plan. They sent this follow-up message.
Classify it as:
- "question": asking for explanation, more detail, or clarification about the plan
- "new_data": providing new financial information or wanting a completely different calculation

Message: "{user_message}"
Reply with ONLY one word: question / new_data"""
    result = get_small_model().invoke([HumanMessage(content=prompt)])
    r = result.content.strip().lower().split()[0]
    return r if r in ("question", "new_data") else "question"


def _answer_followup(state: AgentState, user_message: str) -> AgentState:
    """Answer a follow-up question conversationally using existing plan context."""
    plan = state.calculation_results.get("advisor_plan", {})
    roadmap = state.calculation_results.get("monthly_roadmap", [])
    goal_plan = state.calculation_results.get("goal_plan", {})
    tax = state.calculation_results.get("tax_comparison", {})
    msg_lower = user_message.lower()

    # Detect if user wants the roadmap rendered — return the full plan JSON again
    roadmap_triggers = ["month by month", "monthly plan", "roadmap", "step by step",
                        "in detail", "detailed", "break it down", "breakdown", "elaborate"]
    if any(t in msg_lower for t in roadmap_triggers) and roadmap:
        # Re-send the full advisor plan so frontend renders the cards again
        # but also include the roadmap prominently
        import json as _json
        reply = _json.dumps({
            "headline": plan.get("headline", "Here's your detailed month-by-month plan"),
            "tone_opener": "Here's the full breakdown you asked for:",
            "tax": plan.get("tax"),
            "fire": plan.get("fire"),
            "actions": plan.get("actions"),
            "insight": plan.get("insight"),
            "life_event_advice": plan.get("life_event_advice"),
            "deductions": plan.get("deductions"),
        })
        state.messages.append({"role": "assistant", "content": reply})
        return state

    # Otherwise answer conversationally
    context = f"""You are an Indian financial mentor on Economic Times.
The user already received this financial plan:
{plan}

Tax details: {tax}
Monthly roadmap available: {len(roadmap)} months planned

User's follow-up: "{user_message}"

Answer specifically in 2-4 sentences using exact ₹ numbers from the plan.
Do not repeat the entire plan. Be conversational — like a CA friend explaining over chai."""

    result = get_small_model().invoke([HumanMessage(content=context)])
    reply = result.content.strip()
    state.messages.append({"role": "assistant", "content": reply})
    return state
