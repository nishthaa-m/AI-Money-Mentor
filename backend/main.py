"""FastAPI entry point — chat + streaming + session management."""
from __future__ import annotations
import os
import uuid
import json
import asyncio
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

load_dotenv()

from backend.models.schemas import ChatRequest, ChatResponse, AgentState
from backend.agents.orchestrator import process_message

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
