from dotenv import load_dotenv; load_dotenv()
import requests, json

BASE = "http://localhost:8000"
sid = requests.post(f"{BASE}/session/new").json()["session_id"]

# Simulate the quick-start button click — single message
msg = "Getting married next year. Financial plan?"
r = requests.post(f"{BASE}/chat", json={"session_id": sid, "message": msg}, timeout=60)
d = r.json()
print(f"Turn 1: scenario={d.get('scenario')} complete={d.get('profile_complete')}")
print(f"  reply: {d.get('reply','')[:200]}")

# Check session state
s = requests.get(f"{BASE}/session/{sid}").json()
profile = s.get("profile", {})
print(f"\nProfile after turn 1:")
print(f"  age={profile.get('age')} income={profile.get('annual_income')} life_event={profile.get('life_event')}")
print(f"  missing_fields={s.get('missing_fields')}")
print(f"  iteration_count={s.get('iteration_count')}")
