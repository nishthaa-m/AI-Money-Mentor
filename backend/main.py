"""FastAPI entry point — chat + streaming + session management + Tax Wizard."""
from __future__ import annotations
import os
import uuid
import json
import asyncio
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

load_dotenv()

from backend.models.schemas import ChatRequest, ChatResponse, AgentState
from backend.agents.orchestrator import process_message
from backend.tools.form16_parser import parse_form16
from backend.tools.tax_engine import (
    DeductionProfile, compare_regimes, identify_missed_deductions,
    calculate_tax_with_steps, tax_saving_instruments, calculate_hra_exemption,
)
from backend.tools.compliance import apply_guardrail
from backend.tools.life_events import (
    handle_bonus, handle_inheritance, handle_marriage,
    handle_new_baby, handle_job_change,
)

app = FastAPI(title="AI Money Mentor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: dict[str, dict] = {}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not os.getenv("OPENROUTER_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured in .env")

    existing = sessions.get(req.session_id)
    state = await process_message(req.session_id, req.message, existing)
    sessions[req.session_id] = state.model_dump()

    assistant_msgs = [m for m in state.messages if m["role"] == "assistant"]
    last_reply = assistant_msgs[-1]["content"] if assistant_msgs else ""
    reply = last_reply if last_reply else state.error or "..."

    return ChatResponse(
        session_id=req.session_id,
        reply=reply,
        scenario=state.scenario,
        calculations=state.calculation_results if state.calculation_results else None,
        profile_complete=not bool(state.missing_fields),
    )


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """
    SSE streaming endpoint.
    Emits:
      data: {"type": "token", "content": "..."}   — text tokens as they arrive
      data: {"type": "calculations", "data": {...}} — full calculations when ready
      data: {"type": "done", "scenario": "..."}    — signals completion
    """
    if not os.getenv("OPENROUTER_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured in .env")

    async def event_stream() -> AsyncGenerator[str, None]:
        existing = sessions.get(req.session_id)

        # Run the pipeline — emit status tokens while waiting
        status_messages = [
            "Analysing your query",
            "Collecting your financial details",
            "Running calculations",
            "Preparing your personalised plan",
        ]

        # Start pipeline in background
        pipeline_task = asyncio.create_task(
            process_message(req.session_id, req.message, existing)
        )

        # Emit status tokens while pipeline runs
        for i, status in enumerate(status_messages):
            if pipeline_task.done():
                break
            yield f"data: {json.dumps({'type': 'status', 'content': status})}\n\n"
            try:
                await asyncio.wait_for(asyncio.shield(pipeline_task), timeout=2.0)
                break
            except asyncio.TimeoutError:
                continue

        # Await final result
        state: AgentState = await pipeline_task
        sessions[req.session_id] = state.model_dump()

        assistant_msgs = [m for m in state.messages if m["role"] == "assistant"]
        reply = assistant_msgs[-1]["content"] if assistant_msgs else state.error or "..."

        # Stream the reply character by character for text, or as one chunk for JSON
        is_json = reply.strip().startswith("{")
        if is_json:
            # JSON plan — send as single chunk (can't stream partial JSON)
            yield f"data: {json.dumps({'type': 'plan', 'content': reply})}\n\n"
        else:
            # Plain text — stream word by word
            words = reply.split(" ")
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
                await asyncio.sleep(0.02)  # 20ms between words

        # Send calculations
        if state.calculation_results:
            yield f"data: {json.dumps({'type': 'calculations', 'data': state.calculation_results})}\n\n"

        # Done
        yield f"data: {json.dumps({'type': 'done', 'scenario': state.scenario, 'profile_complete': not bool(state.missing_fields)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/session/new")
async def new_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = AgentState(session_id=session_id).model_dump()
    return {"session_id": session_id}


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


# ── Tax Wizard Endpoints ──────────────────────────────────────────────────────

@app.post("/tax/upload-form16")
async def upload_form16(file: UploadFile = File(...)):
    """Parse Form 16 PDF and return extracted salary structure."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file")
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    pdf_bytes = await file.read()
    extracted = parse_form16(pdf_bytes)

    if "error" in extracted:
        raise HTTPException(status_code=422, detail=extracted["error"])

    return {"extracted": extracted, "message": f"Extracted {len(extracted.get('fields_extracted', []))} fields from Form 16"}


@app.post("/tax/analyze")
async def analyze_tax(data: dict):
    """
    Full tax analysis from salary structure.
    Accepts either Form 16 extracted data or manual input.
    Returns: regime comparison, step-by-step trace, missed deductions, instruments.
    """
    gross = data.get("annual_income", 0)
    if not gross:
        raise HTTPException(status_code=400, detail="annual_income is required")

    age = data.get("age", 30)

    # HRA exemption if applicable
    hra_exempt = data.get("hra_exempt", 0)
    if data.get("hra_received") and not hra_exempt:
        basic = data.get("basic_salary") or gross * 0.40
        rent = data.get("rent_paid") or data.get("hra_received", 0) * 1.2
        hra_calc = calculate_hra_exemption(
            annual_hra_received=data.get("hra_received", 0),
            annual_basic=basic,
            annual_rent_paid=rent,
            metro_city=data.get("metro_city", True),
        )
        hra_exempt = hra_calc["hra_exempt"]
    else:
        hra_calc = None

    deductions = DeductionProfile(
        section_80c=data.get("section_80c_invested", 0),
        section_80d_self=data.get("section_80d_self", 0),
        section_80d_parents=data.get("section_80d_parents", 0),
        section_80ccd1b=data.get("section_80ccd1b", 0),
        hra_exempt=hra_exempt,
        lta=data.get("lta", 0),
        home_loan_interest=data.get("home_loan_interest", 0),
        other_deductions=data.get("other_deductions", 0),
        age=age,
    )

    comparison = compare_regimes(gross, deductions)
    rec = comparison["recommended_regime"]

    steps_new = calculate_tax_with_steps(gross, deductions, "new")
    steps_old = calculate_tax_with_steps(gross, deductions, "old")
    missed = identify_missed_deductions(gross, deductions)
    instruments = tax_saving_instruments(gross, deductions, rec)

    # Potential saving if all deductions maximised under old regime
    max_deductions = DeductionProfile(
        section_80c=150_000,
        section_80d_self=25_000,
        section_80ccd1b=50_000,
        hra_exempt=hra_exempt,
        lta=data.get("lta", 0),
        home_loan_interest=data.get("home_loan_interest", 0),
        age=age,
    )
    max_old = compare_regimes(gross, max_deductions)
    best_possible_tax = min(comparison["new_regime"]["total_tax"], max_old["old_regime"]["total_tax"])
    current_tax = comparison[f"{rec}_regime"]["total_tax"]
    max_saving = round(current_tax - best_possible_tax, 0)

    result = {
        "gross_income": gross,
        "tax_comparison": comparison,
        "tax_steps_new": steps_new,
        "tax_steps_old": steps_old,
        "missed_deductions": missed,
        "tax_instruments": instruments,
        "hra_calculation": hra_calc,
        "summary": {
            "recommended_regime": rec,
            "current_tax": current_tax,
            "effective_rate": comparison[f"{rec}_regime"]["effective_rate_pct"],
            "monthly_tds_should_be": round(current_tax / 12, 0),
            "tds_deducted": data.get("tds_deducted", 0),
            "tds_gap": round(data.get("tds_deducted", 0) - current_tax, 0),
            "max_additional_saving_possible": max(max_saving, 0),
            "total_missed_deduction_gap": sum(d.get("gap", 0) for d in missed),
        },
    }

    return result


# ── Life Events Endpoints ─────────────────────────────────────────────────────

@app.post("/life-events/analyze")
async def analyze_life_event(data: dict):
    """
    Analyze a life event and return a structured financial plan.
    event: bonus | inheritance | marriage | baby | job_change
    """
    event = data.get("event", "").lower()
    if not event:
        raise HTTPException(status_code=400, detail="event field is required")

    try:
        if event == "bonus":
            result = handle_bonus(
                bonus_amount=data.get("amount", 0),
                annual_income=data.get("annual_income", 0),
                monthly_expenses=data.get("monthly_expenses", 0),
                existing_corpus=data.get("existing_corpus", 0),
                age=data.get("age", 30),
                risk_profile=data.get("risk_profile", "moderate"),
                section_80c_invested=data.get("section_80c_invested", 0),
                section_80ccd1b=data.get("section_80ccd1b", 0),
            )
        elif event == "inheritance":
            result = handle_inheritance(
                inheritance_amount=data.get("amount", 0),
                annual_income=data.get("annual_income", 0),
                monthly_expenses=data.get("monthly_expenses", 0),
                existing_corpus=data.get("existing_corpus", 0),
                age=data.get("age", 30),
                risk_profile=data.get("risk_profile", "moderate"),
                has_home_loan=data.get("has_home_loan", False),
                home_loan_outstanding=data.get("home_loan_outstanding", 0),
            )
        elif event == "marriage":
            result = handle_marriage(
                your_income=data.get("annual_income", 0),
                partner_income=data.get("partner_income", 0),
                your_corpus=data.get("existing_corpus", 0),
                partner_corpus=data.get("partner_corpus", 0),
                monthly_expenses_combined=data.get("monthly_expenses", 0),
                your_age=data.get("age", 30),
                risk_profile=data.get("risk_profile", "moderate"),
                planning_home=data.get("planning_home", False),
                planning_child=data.get("planning_child", False),
            )
        elif event == "baby":
            result = handle_new_baby(
                annual_income=data.get("annual_income", 0),
                monthly_expenses=data.get("monthly_expenses", 0),
                existing_corpus=data.get("existing_corpus", 0),
                age=data.get("age", 30),
                risk_profile=data.get("risk_profile", "moderate"),
                is_girl=data.get("is_girl", False),
            )
        elif event == "job_change":
            result = handle_job_change(
                old_income=data.get("old_income", 0),
                new_income=data.get("annual_income", 0),
                joining_bonus=data.get("joining_bonus", 0),
                pf_corpus=data.get("pf_corpus", 0),
                age=data.get("age", 30),
                monthly_expenses=data.get("monthly_expenses", 0),
                risk_profile=data.get("risk_profile", "moderate"),
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown event: {event}. Use: bonus, inheritance, marriage, baby, job_change")

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
