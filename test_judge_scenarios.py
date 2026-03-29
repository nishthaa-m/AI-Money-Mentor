"""Test both judge scenarios before building fixes."""
from dotenv import load_dotenv; load_dotenv()
import requests, json

BASE = "http://localhost:8000"

def run(turns):
    sid = requests.post(f"{BASE}/session/new").json()["session_id"]
    results = []
    for msg in turns:
        r = requests.post(f"{BASE}/chat", json={"session_id": sid, "message": msg}, timeout=90)
        d = r.json()
        results.append(d)
    return sid, results

print("=== SCENARIO 1: FIRE mid-career ===")
sid1, r1 = run([
    "A 34-year-old software engineer earns ₹24L/year, has ₹18L in existing MF investments, ₹6L in PPF, wants to retire at 50 with monthly draw of ₹1.5L (inflation adjusted)",
])
d = r1[-1]
calcs = d.get("calculations") or {}
fire = calcs.get("fire", {})
roadmap = calcs.get("monthly_roadmap", [])
print(f"complete={d.get('profile_complete')} scenario={d.get('scenario')}")
print(f"fire_age={fire.get('fire_age')} corpus_needed={fire.get('fire_number')}")
print(f"roadmap months={len(roadmap)}")
print(f"has glidepath: {'glidepath' in calcs}")
print(f"has sip_by_category: {'sip_by_category' in calcs}")
print()

print("=== SCENARIO 2: Tax edge case ===")
sid2, r2 = run([
    "Base salary ₹18L, HRA ₹3.6L, 80C investments ₹1.5L, NPS ₹50K, home loan interest ₹40K. Calculate exact tax under both regimes, show step by step",
])
d2 = r2[-1]
calcs2 = d2.get("calculations") or {}
tax = calcs2.get("tax_comparison", {})
print(f"complete={d2.get('profile_complete')} scenario={d2.get('scenario')}")
print(f"has tax_steps: {'tax_steps' in calcs2}")
new_tax = tax.get("new_regime", {}).get("total_tax", 0)
old_tax = tax.get("old_regime", {}).get("total_tax", 0)
print(f"new_regime_tax=₹{new_tax:,.0f}  old_regime_tax=₹{old_tax:,.0f}")
print(f"recommended={tax.get('recommended_regime')}")
