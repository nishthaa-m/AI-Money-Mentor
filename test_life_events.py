from dotenv import load_dotenv; load_dotenv()
import requests, json

BASE = "http://localhost:8000"

tests = [
    ("bonus", {"amount": 500000, "annual_income": 1500000, "monthly_expenses": 50000, "existing_corpus": 800000, "age": 30, "section_80c_invested": 50000, "risk_profile": "moderate"}),
    ("marriage", {"annual_income": 1200000, "partner_income": 900000, "existing_corpus": 500000, "partner_corpus": 300000, "monthly_expenses": 80000, "age": 28, "planning_home": True, "planning_child": True}),
    ("baby", {"annual_income": 1500000, "monthly_expenses": 60000, "existing_corpus": 1000000, "age": 32, "is_girl": True}),
    ("job_change", {"old_income": 1200000, "annual_income": 1800000, "joining_bonus": 300000, "pf_corpus": 400000, "monthly_expenses": 50000, "age": 29}),
    ("inheritance", {"amount": 5000000, "annual_income": 1500000, "monthly_expenses": 60000, "existing_corpus": 800000, "age": 35, "has_home_loan": True, "home_loan_outstanding": 3000000}),
]

for event, payload in tests:
    r = requests.post(f"{BASE}/life-events/analyze", json={"event": event, **payload}, timeout=10)
    d = r.json()
    print(f"{event}: status={r.status_code} | checklist={len(d.get('checklist', []))} items")
    if d.get("insight"):
        print(f"  insight: {d['insight'][:80]}")
    print()
