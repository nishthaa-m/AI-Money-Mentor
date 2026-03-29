"""Pydantic schemas for user profile and agent state."""
from __future__ import annotations
from typing import Optional, Literal, Any
from pydantic import BaseModel, Field


class Goal(BaseModel):
    name: str
    target_amount: float
    target_years: int
    existing_corpus: float = 0.0


class UserProfile(BaseModel):
    # Identity
    user_id: str = "anonymous"
    name: Optional[str] = None
    age: Optional[int] = None
    # Income
    annual_income: Optional[float] = None
    spouse_income: Optional[float] = None
    monthly_expenses: Optional[float] = None
    # Investments
    existing_corpus: Optional[float] = None
    existing_mf: float = 0.0          # mutual fund corpus
    existing_ppf: float = 0.0         # PPF corpus
    monthly_sip: Optional[float] = None
    # Insurance
    term_cover: float = 0.0
    health_cover: float = 0.0
    # Tax
    tax_regime: Optional[Literal["old", "new", "unknown"]] = "unknown"
    section_80c_invested: float = 0.0
    section_80d_self: float = 0.0
    section_80d_parents: float = 0.0
    section_80ccd1b: float = 0.0
    hra_received: float = 0.0          # HRA received from employer
    hra_exempt: float = 0.0            # computed HRA exemption
    lta: float = 0.0
    home_loan_interest: float = 0.0
    # Profile
    risk_profile: Literal["conservative", "moderate", "aggressive"] = "moderate"
    dependents: int = 0
    goals: list[Goal] = Field(default_factory=list)
    # FIRE / retirement
    target_retirement_age: Optional[int] = None   # user-specified, e.g. 50
    target_monthly_draw: Optional[float] = None   # desired monthly income at retirement
    # Life event
    life_event: Optional[str] = None
    life_event_amount: Optional[float] = None


class AgentState(BaseModel):
    session_id: str
    user_id: str = "anonymous"
    messages: list[dict] = Field(default_factory=list)
    profile: UserProfile = Field(default_factory=UserProfile)
    scenario: Optional[Literal["tax", "fire", "life_event"]] = None
    calculation_results: dict[str, Any] = Field(default_factory=dict)
    advice_text: str = ""
    missing_fields: list[str] = Field(default_factory=list)
    is_complete: bool = False
    error: Optional[str] = None
    iteration_count: int = 0


class ChatRequest(BaseModel):
    session_id: str
    message: str
    user_id: str = "anonymous"


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    scenario: Optional[str] = None
    calculations: Optional[dict] = None
    profile_complete: bool = False
