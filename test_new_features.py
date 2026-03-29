from dotenv import load_dotenv; load_dotenv()
import requests, json

BASE = "http://localhost:8000"
sid = requests.post(f"{BASE}/session/new").json()["session_id"]

turns = [
    "I want to plan my retirement. I am 30, earning 20 LPA",
    "Monthly expenses 60000, savings 8 lakhs, moderate risk",
]

for msg in turns:
    r = requests.post(f"{BASE}/chat", json={"session_id": sid, "message": msg}, timeout=90)
    d = r.json()
    calcs = d.get("calculations", {}) or {}
    print(f"complete={d.get('profile_complete')} | scenario={d.get('scenario')}")
    if calcs:
        print(f"  literacy_score:   {bool(calcs.get('literacy_score'))} — before={calcs.get('literacy_score', {}).get('before')} after={calcs.get('literacy_score', {}).get('after')}")
        print(f"  monthly_roadmap:  {len(calcs.get('monthly_roadmap', []))} months")
        print(f"  goal_plan:        {bool(calcs.get('goal_plan'))} — {len(calcs.get('goal_plan', {}).get('goals', []))} goals")
        print(f"  fire:             {bool(calcs.get('fire'))}")
    print()
