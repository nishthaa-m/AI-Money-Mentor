from dotenv import load_dotenv; load_dotenv()
import requests, json

BASE = "http://localhost:8000"
sid = requests.post(f"{BASE}/session/new").json()["session_id"]

turns = [
    ("I earn 15 LPA, help me with taxes. I am 28.", "initial"),
    ("What exactly is the 80CCD(1B) deduction?", "followup_question"),
    ("What if I also have a home loan of 30 lakhs?", "new_data"),
]

for msg, kind in turns:
    r = requests.post(f"{BASE}/chat", json={"session_id": sid, "message": msg}, timeout=60)
    d = r.json()
    reply = d.get("reply", "")
    is_json = reply.strip().startswith("{")
    print(f"\n[{kind}] complete={d.get('profile_complete')} | json_plan={is_json}")
    if is_json:
        try:
            p = json.loads(reply[reply.index("{"):reply.rindex("}")+1])
            print(f"  headline: {p.get('headline','')[:80]}")
        except: pass
    else:
        print(f"  reply: {reply[:200]}")
