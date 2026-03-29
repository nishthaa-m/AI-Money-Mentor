from dotenv import load_dotenv; load_dotenv()
import requests, json

BASE = "http://localhost:8000"

# Test 1: Complex first message with all data
sid = requests.post(f"{BASE}/session/new").json()["session_id"]
msg = "A 34-year-old software engineer earns ₹24L/year, has ₹18L in existing MF investments, ₹6L in PPF, and wants to retire at 50 with a monthly corpus draw of ₹1.5L (today's value, inflation adjusted). produce a month-by-month plan: SIP amounts by fund category, asset allocation glidepath, insurance gap analysis, and estimated retirement date given current trajectory."

r = requests.post(f"{BASE}/chat", json={"session_id": sid, "message": msg}, timeout=90)
d = r.json()
s = requests.get(f"{BASE}/session/{sid}").json()
profile = s.get("profile", {})
print("=== Complex first message ===")
print(f"scenario={d.get('scenario')} complete={d.get('profile_complete')}")
print(f"profile: age={profile.get('age')} income={profile.get('annual_income')} corpus={profile.get('existing_corpus')}")
print(f"missing={s.get('missing_fields')}")
reply = d.get("reply", "")
print(f"reply: {reply[:150]}")

print()

# Test 2: "24 lakhs" as follow-up
sid2 = requests.post(f"{BASE}/session/new").json()["session_id"]
turns2 = [
    "I want to plan my retirement, I am 34",
    "24 lakhs",
]
for msg in turns2:
    r = requests.post(f"{BASE}/chat", json={"session_id": sid2, "message": msg}, timeout=60)
    d = r.json()
    s = requests.get(f"{BASE}/session/{sid2}").json()
    profile = s.get("profile", {})
    print(f"'{msg}' → income={profile.get('annual_income')} complete={d.get('profile_complete')}")
