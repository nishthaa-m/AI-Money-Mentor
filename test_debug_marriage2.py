from dotenv import load_dotenv; load_dotenv()
import requests, json

BASE = "http://localhost:8000"
sid = requests.post(f"{BASE}/session/new").json()["session_id"]

turns = [
    "Getting married next year. Financial plan?",
    "I am 27",           # gives age only
    "I earn 18 LPA",     # gives income
]

for i, msg in enumerate(turns):
    r = requests.post(f"{BASE}/chat", json={"session_id": sid, "message": msg}, timeout=60)
    d = r.json()
    s = requests.get(f"{BASE}/session/{sid}").json()
    profile = s.get("profile", {})
    reply = d.get("reply", "")
    is_json = reply.strip().startswith("{")

    print(f"\nTurn {i+1}: '{msg}'")
    print(f"  scenario={d.get('scenario')} complete={d.get('profile_complete')} json={is_json}")
    print(f"  profile: age={profile.get('age')} income={profile.get('annual_income')} life_event={profile.get('life_event')}")
    print(f"  missing={s.get('missing_fields')} iterations={s.get('iteration_count')}")
    if is_json:
        try:
            p = json.loads(reply[reply.index("{"):reply.rindex("}")+1])
            print(f"  headline: {p.get('headline','')[:80]}")
            print(f"  has_fire: {p.get('fire') is not None}")
            print(f"  life_event_advice: {str(p.get('life_event_advice',''))[:100]}")
        except: pass
    else:
        print(f"  reply: {reply[:120]}")
