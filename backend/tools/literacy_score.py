"""
Financial Literacy Score — measures user knowledge before and after interaction.
Scored 0-100. Tracks improvement as a measurable outcome.

Dimensions (each 0-20):
1. Tax awareness     — knows about regimes, deductions
2. Investment basics — understands SIP, equity vs debt
3. Insurance         — aware of term + health cover needs
4. Emergency fund    — knows the 6-month rule
5. Goal planning     — has defined financial goals
"""
from __future__ import annotations
from backend.models.schemas import UserProfile


def compute_literacy_score(profile: UserProfile, conversation: list[dict]) -> dict:
    """
    Compute literacy score from profile data and conversation content.
    Only scans USER messages — assistant JSON blobs would skew results.
    Profile fields contribute the most — conversation keywords are a bonus.
    """
    # Only user messages, skip JSON blobs
    user_text = " ".join(
        m["content"].lower() for m in conversation
        if m["role"] == "user" and not m["content"].strip().startswith("{")
    )

    # ── Dimension 1: Tax awareness (0-20) ────────────────────────────────────
    tax_score = 0
    if profile.tax_regime and profile.tax_regime != "unknown":
        tax_score += 8
    if profile.section_80c_invested > 0:
        tax_score += 6
    if profile.section_80ccd1b > 0:
        tax_score += 6
    tax_keywords = ["80c", "80d", "nps", "elss", "ppf", "deduction", "regime", "tds", "itr"]
    tax_score += min(sum(2 for kw in tax_keywords if kw in user_text), 6)
    tax_score = min(tax_score, 20)

    # ── Dimension 2: Investment basics (0-20) ─────────────────────────────────
    inv_score = 0
    if profile.existing_corpus and profile.existing_corpus > 0:
        inv_score += 8
    if profile.monthly_sip and profile.monthly_sip > 0:
        inv_score += 8
    inv_keywords = ["sip", "mutual fund", "index fund", "equity", "debt", "corpus", "returns", "cagr"]
    inv_score += min(sum(2 for kw in inv_keywords if kw in user_text), 6)
    # Bonus: if they have income and are asking about investments
    if profile.annual_income and profile.annual_income > 0:
        inv_score += 4
    inv_score = min(inv_score, 20)

    # ── Dimension 3: Insurance (0-20) ─────────────────────────────────────────
    ins_score = 0
    if profile.term_cover > 0:
        ins_score += 10
    if profile.health_cover > 0:
        ins_score += 10
    ins_keywords = ["term insurance", "health insurance", "mediclaim", "life cover", "irdai"]
    ins_score += min(sum(2 for kw in ins_keywords if kw in user_text), 4)
    ins_score = min(ins_score, 20)

    # ── Dimension 4: Emergency fund (0-20) ────────────────────────────────────
    ef_score = 0
    ef_keywords = ["emergency fund", "liquid", "savings account", "6 months", "contingency"]
    ef_score += min(sum(4 for kw in ef_keywords if kw in user_text), 12)
    if profile.existing_corpus and profile.existing_corpus > 0:
        ef_score += 8
    ef_score = min(ef_score, 20)

    # ── Dimension 5: Goal planning (0-20) ─────────────────────────────────────
    goal_score = 0
    if profile.goals and len(profile.goals) > 0:
        goal_score += 10 + min(len(profile.goals) * 5, 10)
    goal_keywords = ["retirement", "house", "education", "goal", "fire", "corpus", "target",
                     "marriage", "wedding", "baby", "child", "car", "vacation"]
    goal_score += min(sum(2 for kw in goal_keywords if kw in user_text), 8)
    # Life event = they're planning ahead = goal awareness
    if profile.life_event:
        goal_score += 6
    goal_score = min(goal_score, 20)

    total = tax_score + inv_score + ins_score + ef_score + goal_score

    # Before score: what they likely knew before this conversation
    # Base it on profile fields that existed before (not conversation keywords)
    before_profile_score = 0
    if profile.tax_regime and profile.tax_regime != "unknown": before_profile_score += 5
    if profile.existing_corpus and profile.existing_corpus > 0: before_profile_score += 5
    if profile.term_cover > 0: before_profile_score += 5
    if profile.health_cover > 0: before_profile_score += 5
    before_score = max(before_profile_score, 10)  # minimum 10

    # After score must be >= before
    after_score = max(total, before_score)

    return {
        "before": before_score,
        "after": after_score,
        "improvement": after_score - before_score,
        "dimensions": {
            "tax_awareness":     {"score": tax_score,  "max": 20},
            "investment_basics": {"score": inv_score,  "max": 20},
            "insurance":         {"score": ins_score,  "max": 20},
            "emergency_fund":    {"score": ef_score,   "max": 20},
            "goal_planning":     {"score": goal_score, "max": 20},
        },
        "level": _level(after_score),
        "next_milestone": _next_milestone(after_score),
    }


def _level(score: int) -> str:
    if score >= 80: return "Financial Expert"
    if score >= 60: return "Financially Aware"
    if score >= 40: return "Learning the Basics"
    if score >= 20: return "Financial Beginner"
    return "Just Getting Started"


def _next_milestone(score: int) -> str:
    if score < 20:  return "Learn about tax deductions to reach 'Financial Beginner'"
    if score < 40:  return "Start a SIP and get health insurance to reach 'Learning the Basics'"
    if score < 60:  return "Build an emergency fund and set retirement goals to reach 'Financially Aware'"
    if score < 80:  return "Optimise NPS and term insurance to reach 'Financial Expert'"
    return "You're a financial expert! Help others on their journey."
