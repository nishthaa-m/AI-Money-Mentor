from dotenv import load_dotenv; load_dotenv()
import requests, json

BASE = "http://localhost:8000"

sid = requests.post(f"{BASE}/session/new").json()["session_id"]

turns = [
    "Getting married next year. Financial plan?",
    "I am 27, earning 18 LPA",
]

for msg in turns:
    r = requests.post(f"{BASE}/chat", json={"session_id": sid, "message": msg}, timeout=90)
    d = r.json()
    reply = d.get("reply", "")
    is_json = reply.strip().startswith("{")
    print(f"scenario={d.get('scenario')} | complete={d.get('profile_complete')} | json={is_json}")
    if is_json:
        try:
            p = json.loads(reply[reply.index("{"):reply.rindex("}")+1])
            print(f"  headline:          {p.get('headline','')[:80]}")
            print(f"  life_event_advice: {str(p.get('life_event_advice',''))[:150]}")
            print(f"  has_fire:          {p.get('fire') is not None}")
            print(f"  actions[0]:        {p.get('actions', [{}])[0].get('action','')[:80]}")
        except Exception as e:
            print(f"  parse error: {e}")
    else:
        print(f"  reply: {reply[:120]}")
    print()
