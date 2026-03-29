"""
Profiler Agent — drives conversation to collect user financial data.
Extracts profile fields from conversation, asks targeted follow-ups.
"""
from __future__ import annotations
import os
import json
import re
from functools import lru_cache
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

from backend.models.schemas import AgentState, UserProfile, Goal


@lru_cache(maxsize=1)
def get_small_model():
    key = os.getenv("OPENROUTER_API_KEY")
    if not key or key == "your_openrouter_api_key_here":
        raise RuntimeError("OPENROUTER_API_KEY not set in .env")
    return ChatOpenAI(
        model="meta-llama/llama-3.1-8b-instruct",
        temperature=0.1,
        base_url="https://openrouter.ai/api/v1",
        api_key=key,
        default_headers={"HTTP-Referer": "http://localhost:3000", "X-Title": "AI Money Mentor"},
    )


REQUIRED_FIELDS_BY_SCENARIO = {
    "tax":        ["age", "annual_income"],
    "fire":       ["age", "annual_income", "monthly_expenses", "existing_corpus"],
    # Life events only need income + age — don't block on corpus/expenses
    "life_event": ["age", "annual_income"],
    "unknown":    ["age", "annual_income"],
}

EXTRACT_PROMPT = """You are extracting financial data from a conversation for an Indian finance app.

Read the ENTIRE conversation and extract financial data. Return ONLY valid JSON, no explanation.

CRITICAL PARSING RULES for Indian income notation:
- "X LPA" or "X lpa" = X lakhs per annum = X * 100,000 (e.g. "15 LPA" = 1,500,000; "50 LPA" = 5,000,000)
- "₹XL/year" or "₹X lakhs" = X * 100,000 (e.g. "₹24L/year" = 2,400,000; "₹18 lakhs" = 1,800,000)
- "X lakhs" = X * 100,000 (e.g. "15 lakhs" = 1,500,000)
- "X crore" = X * 10,000,000
- "X k/month" = X * 1,000 * 12 annual (e.g. "50k/month" = 600,000 annual)
- "X per month" salary = X * 12 annual
- NEVER confuse LPA (lakhs per annum) with thousands — 50 LPA = 50,00,000 NOT 50,000
- ₹ symbol before a number does NOT change the value — ₹24L = 24 lakhs = 2,400,000

JSON fields (null if not mentioned):
{{
  "age": <integer — ONLY if explicitly stated, e.g. "I am 34" or "34-year-old">,
  "annual_income": <ANNUAL income in rupees — apply rules above carefully>,
  "monthly_expenses": <TOTAL monthly expenses — sum all items if listed>,
  "existing_corpus": <total investments in rupees — use if no breakdown given>,
  "existing_mf": <mutual fund corpus in rupees — if specifically mentioned>,
  "existing_ppf": <PPF corpus in rupees — if specifically mentioned>,
  "risk_profile": <"conservative"|"moderate"|"aggressive"|null>,
  "dependents": <integer>,
  "life_event": <"bonus"|"marriage"|"baby"|"inheritance"|"job_change"|null>,
  "life_event_amount": <amount in rupees>,
  "section_80c_invested": <amount in rupees>,
  "section_80ccd1b": <NPS contribution in rupees>,
  "hra_received": <annual HRA received from employer in rupees>,
  "home_loan_interest": <annual home loan interest in rupees>,
  "target_retirement_age": <integer — if user says "retire at 50" → 50>,
  "target_monthly_draw": <desired monthly income at retirement in rupees — if mentioned>,
  "tax_regime": <"old"|"new"|"unknown">
}}

CONVERSATION:
{conversation}"""

FOLLOWUP_PROMPT = """You are a warm Indian financial assistant collecting data for a {scenario} planning tool on Economic Times.

Current collected data: {profile_json}
Still need: {missing_fields}

Ask ONE natural follow-up question to get the next missing piece.
Be conversational, use Indian context (₹, lakhs etc.).
Do NOT give financial advice yet. Just collect data.
Keep it to 1-2 sentences max.
Do NOT mention retirement or FIRE unless the scenario is fire."""


def _conversation_text(messages: list[dict]) -> str:
    lines = []
    for m in messages:
        role = "User" if m["role"] == "user" else "Assistant"
        lines.append(f"{role}: {m['content']}")
    return "\n".join(lines)


def _regex_pre_extract(messages: list[dict]) -> dict:
    """
    Fast regex extraction for common patterns before LLM.
    Handles: age, income (LPA/lakhs/₹XL), corpus mentions.
    """
    user_text = " ".join(m["content"] for m in messages if m["role"] == "user")
    clean = user_text.replace("₹", " ").replace(",", "").lower()
    result = {}

    # Age: "34-year-old", "I am 34", "age 34", "34 years"
    age_patterns = [
        r'(\d+)[- ]year[s]?[- ]old',
        r'\bi\s+am\s+(\d+)',
        r'\bage\s+(\d+)',
        r'(\d+)\s+years?\s+old',
        r'\baged?\s+(\d+)',
    ]
    for pat in age_patterns:
        m = re.search(pat, clean)
        if m:
            age = int(m.group(1))
            if 18 <= age <= 75:
                result["age"] = age
                break

    # Income: ₹XL/year, X LPA, X lakhs/year
    income_patterns = [
        (r'earns?\s+(\d+(?:\.\d+)?)\s*l(?:/year|/yr|pa)?', 100_000),
        (r'(\d+(?:\.\d+)?)\s*lpa\b', 100_000),
        (r'(\d+(?:\.\d+)?)\s*lakhs?\s*(?:per\s*year|/year|p\.?a\.?|annual)', 100_000),
        (r'income\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*l', 100_000),
        (r'salary\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*l', 100_000),
        (r'(\d+(?:\.\d+)?)\s*l\s*/\s*year', 100_000),
    ]
    for pat, multiplier in income_patterns:
        m = re.search(pat, clean)
        if m:
            val = float(m.group(1)) * multiplier
            if 100_000 <= val <= 100_000_000:
                result["annual_income"] = val
                break

    # Corpus: "₹18L in MF", "18 lakhs in investments"
    corpus_patterns = [
        r'(\d+(?:\.\d+)?)\s*l\s+in\s+(?:existing|mf|mutual|ppf|investments?|savings?)',
        r'(?:existing|current|total)\s+(?:corpus|savings?|investments?)\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*l',
    ]
    corpus_total = 0.0
    for pat in corpus_patterns:
        for m in re.finditer(pat, clean):
            corpus_total += float(m.group(1)) * 100_000
    if corpus_total > 0:
        result["existing_corpus"] = corpus_total

    # Life event
    if any(w in clean for w in ["married", "marriage", "wedding", "getting married"]):
        result["life_event"] = "marriage"
    elif any(w in clean for w in ["bonus", "got a bonus", "received bonus"]):
        result["life_event"] = "bonus"
    elif any(w in clean for w in ["baby", "pregnant", "child", "newborn"]):
        result["life_event"] = "baby"
    elif any(w in clean for w in ["inheritance", "inherited", "will", "estate"]):
        result["life_event"] = "inheritance"

    # Retirement age: "retire at 50", "retirement at 55"
    retire_match = re.search(r'retire\s+(?:at|by|before)\s+(\d+)', clean)
    if retire_match:
        age_val = int(retire_match.group(1))
        if 40 <= age_val <= 70:
            result["target_retirement_age"] = age_val

    # Monthly draw at retirement: "monthly draw of ₹1.5L", "₹1.5L per month"
    draw_patterns = [
        r'(?:monthly\s+(?:draw|income|corpus\s+draw|withdrawal))\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*l',
        r'(\d+(?:\.\d+)?)\s*l\s+(?:per\s+month|/month)\s+(?:at|after|post)\s+retirement',
    ]
    for pat in draw_patterns:
        m = re.search(pat, clean)
        if m:
            result["target_monthly_draw"] = float(m.group(1)) * 100_000
            break

    # MF corpus: "₹18L in MF", "18 lakhs in mutual funds"
    mf_match = re.search(r'(\d+(?:\.\d+)?)\s*l\s+in\s+(?:existing\s+)?(?:mf|mutual\s+fund)', clean)
    if mf_match:
        result["existing_mf"] = float(mf_match.group(1)) * 100_000

    # PPF corpus: "₹6L in PPF"
    ppf_match = re.search(r'(\d+(?:\.\d+)?)\s*l\s+in\s+ppf', clean)
    if ppf_match:
        result["existing_ppf"] = float(ppf_match.group(1)) * 100_000

    # NPS / 80CCD(1B)
    nps_match = re.search(r'nps\s+(?:contribution\s+of\s+)?(\d+(?:\.\d+)?)\s*(?:k|l)?', clean)
    if nps_match:
        val = float(nps_match.group(1))
        suffix_pos = nps_match.end()
        if 'k' in clean[nps_match.start():suffix_pos+2]:
            val *= 1000
        elif 'l' in clean[nps_match.start():suffix_pos+2]:
            val *= 100_000
        result["section_80ccd1b"] = val

    # HRA received
    hra_match = re.search(r'hra\s+(?:component\s+of\s+|of\s+)?(\d+(?:\.\d+)?)\s*l', clean)
    if hra_match:
        result["hra_received"] = float(hra_match.group(1)) * 100_000

    return result
    lines = []
    for m in messages:
        role = "User" if m["role"] == "user" else "Assistant"
        lines.append(f"{role}: {m['content']}")
    return "\n".join(lines)


def _regex_extract_expenses(messages: list[dict]) -> int | None:
    """Fallback: sum all rupee amounts mentioned in user messages about expenses."""
    expense_keywords = r"(rent|groceries|grocery|food|travel|utilities|other|necessit|expense)"
    total = 0
    found = False
    for m in messages:
        if m["role"] != "user":
            continue
        text = m["content"].lower()
        if not re.search(expense_keywords, text):
            continue
        # Find all numbers (with optional k/lakh suffix)
        amounts = re.findall(r"₹?\s*(\d+(?:\.\d+)?)\s*(k|lakh|l)?", text)
        for num_str, suffix in amounts:
            num = float(num_str)
            if suffix == "k":
                num *= 1000
            elif suffix in ("lakh", "l"):
                num *= 100000
            # Ignore implausibly large numbers (likely annual income, not expenses)
            if 500 < num < 500000:
                total += num
                found = True
    return int(total) if found and total > 0 else None


def _extract_profile(messages: list[dict], current: UserProfile) -> UserProfile:
    """Extract profile fields — regex pre-extraction first, then LLM for remainder."""
    # Step 1: fast regex pre-extraction (no LLM cost, no hallucination)
    pre = _regex_pre_extract(messages)
    pre_profile = current.model_dump()
    for k, v in pre.items():
        if v is not None and k in pre_profile and pre_profile[k] is None:
            pre_profile[k] = v
    profile = UserProfile(**pre_profile)

    # Step 2: LLM extraction for anything regex missed
    convo = _conversation_text(messages)
    prompt = EXTRACT_PROMPT.format(conversation=convo)
    try:
        result = get_small_model().invoke([HumanMessage(content=prompt)])
        text = result.content.strip()
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        data = json.loads(text)

        user_text = " ".join(m["content"] for m in messages if m["role"] == "user").lower()
        for k, v in data.items():
            if v is None or k not in profile.model_dump():
                continue
            # Skip if already set by regex
            if getattr(profile, k, None) is not None:
                continue
            # Validate numeric fields against conversation text
            if k == "age" and isinstance(v, (int, float)):
                if _number_mentioned(user_text, v, tolerance=2):
                    pre_profile[k] = int(v)
            elif k == "annual_income" and isinstance(v, (int, float)):
                if _income_mentioned(user_text, v):
                    pre_profile[k] = v
            elif k in ("monthly_expenses", "existing_corpus", "life_event_amount") and isinstance(v, (int, float)):
                if _number_mentioned_approx(user_text, v):
                    pre_profile[k] = v
            else:
                pre_profile[k] = v

        profile = UserProfile(**pre_profile)
    except Exception:
        pass

    # Step 3: regex fallback for monthly_expenses
    if not profile.monthly_expenses:
        fallback = _regex_extract_expenses(messages)
        if fallback:
            profile = profile.model_copy(update={"monthly_expenses": fallback})
    return profile


def _number_mentioned(text: str, value: float, tolerance: int = 0) -> bool:
    """Check if a number close to `value` appears in the text."""
    clean = text.replace("₹", "").replace(",", "")
    nums = re.findall(r'\b(\d+(?:\.\d+)?)\b', clean)
    for n in nums:
        if abs(float(n) - value) <= tolerance:
            return True
    return False


def _income_mentioned(text: str, annual_value: float) -> bool:
    """Check if the income value (or its monthly/lpa equivalent) is mentioned."""
    # Normalize: remove ₹ and commas for easier matching
    clean = text.replace("₹", "").replace(",", "").lower()

    # LPA: "24 lpa", "24lpa"
    for m in re.findall(r'(\d+(?:\.\d+)?)\s*lpa\b', clean, re.IGNORECASE):
        if abs(float(m) * 100_000 - annual_value) < 100_000:
            return True

    # Lakhs/L: "24 lakhs", "24l", "24l/year", "₹24L"
    for m in re.findall(r'(\d+(?:\.\d+)?)\s*(?:lakhs?|lacs?|l\b)', clean, re.IGNORECASE):
        if abs(float(m) * 100_000 - annual_value) < 100_000:
            return True

    # Crore
    for m in re.findall(r'(\d+(?:\.\d+)?)\s*crore', clean, re.IGNORECASE):
        if abs(float(m) * 10_000_000 - annual_value) < 500_000:
            return True

    # Raw large number (e.g. "2400000")
    for m in re.findall(r'\b(\d{6,})\b', clean):
        if abs(float(m) - annual_value) < 100_000:
            return True

    # Monthly salary: "200000/month", "2L/month"
    for m in re.findall(r'(\d+(?:\.\d+)?)\s*(?:per month|/month|pm\b)', clean, re.IGNORECASE):
        if abs(float(m) * 12 - annual_value) < 100_000:
            return True

    return False


def _number_mentioned_approx(text: str, value: float) -> bool:
    """Check if a number within 20% of value appears in text."""
    nums = re.findall(r'\b(\d+(?:\.\d+)?)\b', text)
    for n in nums:
        n_val = float(n)
        if n_val > 0 and abs(n_val - value) / max(value, 1) < 0.2:
            return True
    return False


def _get_missing_fields(profile: UserProfile, scenario: str) -> list[str]:
    required = REQUIRED_FIELDS_BY_SCENARIO.get(scenario, REQUIRED_FIELDS_BY_SCENARIO["unknown"])
    return [f for f in required if getattr(profile, f, None) is None]


def run_profiler(state: AgentState) -> AgentState:
    scenario = state.scenario or "unknown"

    # Step 1: extract whatever we can from the full conversation so far
    state.profile = _extract_profile(state.messages, state.profile)
    missing = _get_missing_fields(state.profile, scenario)
    state.missing_fields = missing

    # Profile is complete — no follow-up needed
    if not missing:
        return state

    # Loop guard: after 6 user turns, apply safe defaults rather than loop forever
    user_turns = sum(1 for m in state.messages if m["role"] == "user")
    if user_turns >= 6:
        defaults = {
            "monthly_expenses": (state.profile.annual_income or 1200000) // 24,
            "existing_corpus": 0,
            "age": 28,
            "annual_income": 600000,
        }
        updated = state.profile.model_dump()
        for field in missing:
            if field in defaults:
                updated[field] = defaults[field]
        state.profile = UserProfile(**updated)
        state.missing_fields = []
        return state

    # Step 2: ask for the next missing field
    profile_summary = {
        k: v for k, v in state.profile.model_dump().items()
        if v is not None and k in ("age", "annual_income", "monthly_expenses", "existing_corpus", "risk_profile")
    }
    prompt = FOLLOWUP_PROMPT.format(
        profile_json=json.dumps(profile_summary),
        missing_fields=", ".join(missing),
        scenario=scenario,
    )
    response = get_small_model().invoke([HumanMessage(content=prompt)])
    state.messages.append({"role": "assistant", "content": response.content.strip()})

    return state
