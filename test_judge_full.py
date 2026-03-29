from dotenv import load_dotenv; load_dotenv()
import requests, json

BASE = "http://localhost:8000"

def chat(sid, msg):
    r = requests.post(f"{BASE}/chat", json={"session_id": sid, "message": msg}, timeout=90)
    return r.json()

def new_session():
    return requests.post(f"{BASE}/session/new").json()["session_id"]

print("=== SCENARIO 1: FIRE mid-career ===")
sid1 = new_session()
turns = [
    "A 34-year-old software engineer earns ₹24L/year, has ₹18L in existing MF investments, ₹6L in PPF, wants to retire at 50 with monthly draw of ₹1.5L (inflation adjusted)",
    "monthly expenses around 80000, moderate risk",
]
for msg in turns:
    d = chat(sid1, msg)
    calcs = d.get("calculations") or {}
    fire = calcs.get("fire", {})
    print(f"  complete={d.get('profile_complete')} | scenario={d.get('scenario')}")
    if fire:
        print(f"  target_retirement_age={fire.get('target_retirement_age')}")
        print(f"  fire_number=₹{fire.get('fire_number',0):,.0f}")
        print(f"  monthly_sip_needed=₹{fire.get('monthly_sip_needed',0):,.0f}")
        print(f"  actual_retire_age={fire.get('actual_retirement_age_at_current_rate')}")
        print(f"  on_track={fire.get('on_track')}")
        print(f"  has glidepath: {bool(calcs.get('glidepath'))}")
        print(f"  sip_categories: {len(calcs.get('sip_by_category',[]))}")
        print(f"  roadmap months: {len(calcs.get('monthly_roadmap',[]))}")

print()
print("=== SCENARIO 2: Tax edge case ===")
sid2 = new_session()
d2 = chat(sid2, "Base salary ₹18L, HRA ₹3.6L, 80C investments ₹1.5L, NPS ₹50K, home loan interest ₹40K. I am 32. Calculate exact tax under both regimes step by step")
calcs2 = d2.get("calculations") or {}
tax = calcs2.get("tax_comparison", {})
print(f"  complete={d2.get('profile_complete')} | scenario={d2.get('scenario')}")
print(f"  new_tax=₹{tax.get('new_regime',{}).get('total_tax',0):,.0f}")
print(f"  old_tax=₹{tax.get('old_regime',{}).get('total_tax',0):,.0f}")
print(f"  recommended={tax.get('recommended_regime')}")
print(f"  has tax_steps_new: {bool(calcs2.get('tax_steps_new'))}")
print(f"  steps count: {len(calcs2.get('tax_steps_new',{}).get('steps',[]))}")
print(f"  instruments: {len(calcs2.get('tax_instruments',[]))}")
instr = calcs2.get("tax_instruments", [])
for i in instr:
    print(f"    {i.get('rank')}. {i.get('instrument')} — liquidity: {i.get('liquidity','')[:30]}")
