# AI Money Mentor — Economic Times

> AI-powered personal finance mentor that turns confused savers into confident investors. Built for the ET GenAI Hackathon, Track 9.

![ET Theme](https://img.shields.io/badge/Economic%20Times-AI%20Money%20Mentor-e8001c?style=flat-square)
![FY2025-26](https://img.shields.io/badge/Tax%20Engine-FY%202025--26-green?style=flat-square)
![SEBI Compliant](https://img.shields.io/badge/SEBI-Compliant-blue?style=flat-square)

---

## What It Does

A multi-agent financial planning system with three core capabilities:

- **Tax Wizard** — Old vs new regime comparison (FY2025-26), step-by-step verifiable tax calculation, HRA exemption formula, missed deductions, instruments ranked by liquidity + risk
- **FIRE Planner** — Custom retirement age, inflation-adjusted corpus target, SIP by fund category, year-by-year asset allocation glidepath, 12-month action roadmap
- **Life Event Advisor** — Marriage, bonus, baby, inheritance — personalised allocation plans for each

---

## Architecture

```
User Message
     │
     ▼
Orchestrator (intent detection, follow-up routing)
     │
     ├── Profiler Agent      (gpt-4o-mini / llama-3.1-8b — data collection)
     ├── Calculator Agent    (pure Python — zero LLM, deterministic)
     ├── Advisor Agent       (gemini-2.0-flash — plan generation)
     └── Compliance Layer    (SEBI guardrail, audit log — always last)
```

**Smart model routing** (Technical Creativity rubric):
- Data collection → `llama-3.1-8b` (fast, cheap)
- Routing/classification → `llama-3.1-8b`
- Financial advice → `gemini-2.0-flash` (structured JSON)
- Math/calculations → No LLM (pure Python)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, Tailwind CSS, Recharts |
| Backend | FastAPI, Python 3.13 |
| AI | LangChain, OpenRouter API |
| Models | Llama 3.1 8B (profiling), Gemini 2.0 Flash (advice) |
| Streaming | Server-Sent Events (SSE) |

---

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenRouter API key ([openrouter.ai/keys](https://openrouter.ai/keys))

### Backend

```bash
pip install -r requirements.txt
```

Create `.env` in the root:
```
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

Start the server:
```bash
python -m uvicorn backend.main:app --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Judge Scenarios (Track 9)

### Scenario 1 — FIRE Mid-Career Professional
> "A 34-year-old software engineer earns ₹24L/year, has ₹18L in MF investments, ₹6L in PPF, wants to retire at 50 with ₹1.5L/month draw (inflation adjusted)"

What the agent produces:
- Inflation-adjusted FIRE corpus target
- Monthly SIP needed vs current savings rate
- Actual retirement age at current trajectory + `on_track` flag
- SIP breakdown by fund category (large-cap index, flexi-cap, mid-cap, PPF, debt)
- Year-by-year asset allocation glidepath (equity reduces as retirement approaches)
- 12-month action roadmap with running corpus
- Dynamic recalculation when retirement age changes (e.g. 50 → 55)

### Scenario 2 — Tax Regime Edge Case
> "Base salary ₹18L, HRA ₹3.6L, 80C ₹1.5L, NPS ₹50K, home loan interest ₹40K"

What the agent produces:
- HRA exemption via 3-limit formula (Sec 10(13A))
- Step-by-step tax trace for both regimes (verifiable, not just final answer)
- Exact tax liability: New ₹1,50,800 vs Old ₹1,73,784 → New regime wins
- Missed deductions identified with ₹ saving at marginal rate
- Tax-saving instruments ranked by liquidity (NPS → ELSS → PPF → 80D)

---

## Key Features

### Tax Engine (FY 2025-26)
- Finance Act 2025 slabs: 0-4L=0%, 4-8L=5%, 8-12L=10%, 12-16L=15%, 16-20L=20%, 20-24L=25%, >24L=30%
- Zero tax up to ₹12.75L gross (rebate u/s 87A)
- Marginal relief at the ₹12L threshold
- HRA exemption: `min(actual HRA, 50% basic, rent - 10% basic)`
- Surcharge: 10%/15%/25%/37% for income >50L/1Cr/2Cr/5Cr
- 4% Health & Education Cess

### FIRE Calculator
- Safe Withdrawal Rate: 3.5% (conservative for India)
- Equity CAGR: 12% (Nifty 50 long-term average)
- Inflation: 6% (RBI target band)
- Emergency fund: 6 months expenses

### SEBI Compliance
- Every response appended with SEBI (Investment Advisers) Regulations 2013 disclaimer
- No specific fund/stock recommendations — only categories
- Audit log (JSONL) for every interaction
- Language softening: "consider" not "you must buy"

### Financial Literacy Score
- 5 dimensions: Tax Awareness, Investments, Insurance, Emergency Fund, Goal Planning
- Before/after score per session
- Measurable improvement metric

---

## Project Structure

```
├── backend/
│   ├── agents/
│   │   ├── orchestrator.py     # Pipeline routing, follow-up handling
│   │   ├── profiler.py         # Data collection with hallucination guard
│   │   ├── calculator.py       # Pure math, zero LLM
│   │   └── advisor.py          # JSON plan generation
│   ├── tools/
│   │   ├── tax_engine.py       # FY2025-26 tax calculations
│   │   ├── calculations.py     # FIRE, SIP, glidepath, roadmap
│   │   ├── literacy_score.py   # Financial literacy scoring
│   │   └── compliance.py       # SEBI guardrail + audit log
│   ├── models/schemas.py       # Pydantic schemas
│   └── main.py                 # FastAPI + SSE streaming
├── frontend/
│   ├── app/
│   │   ├── page.tsx            # Main chat UI
│   │   └── globals.css         # ET theme (red #e8001c)
│   ├── components/
│   │   ├── chat/MessageBubble.tsx   # JSON plan renderer
│   │   ├── TaxSteps.tsx             # Step-by-step tax trace
│   │   ├── SipByCategory.tsx        # SIP fund breakdown
│   │   ├── GoalPlan.tsx             # Goal-based SIP planner
│   │   ├── MonthlyRoadmap.tsx       # 12-month action plan
│   │   ├── LiteracyScore.tsx        # Before/after score
│   │   └── charts/                  # Recharts visualizations
│   └── lib/api.ts              # Streaming API client
└── requirements.txt
```

---

## Regulatory Compliance

This system is built in accordance with:
- **SEBI (Investment Advisers) Regulations, 2013** — no unlicensed advisory
- **Income Tax Act, 1961** — all tax figures cite relevant sections
- **Finance Act 2025** — FY2025-26 slabs and rebates
- **IRDAI** — insurance recommendations follow IRDAI thumb rules

All AI outputs include a mandatory disclaimer distinguishing AI guidance from licensed financial advice.

---

*Built for ET GenAI Hackathon 2025 — Track 9: AI Money Mentor*
