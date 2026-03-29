from dotenv import load_dotenv; load_dotenv()
import requests, json

BASE = "http://localhost:8000"

def chat_session(turns):
    sid = requests.post(f"{BASE}/session/new").json()["session_id"]
    for msg in turns:
        r = requests.post(f"{BASE}/chat", json={"session_id": sid, "message": msg}, timeout=60)
        d = r.json()
        reply = d.get("reply", "")
        is_json = reply.strip().startswith("{")
        plan = json.loads(reply[reply.index("{"):reply.rindex("}")+1]) if is_json else None
        print(f"  scenario={d.get('scenario')} | complete={d.get('profile_complete')} | json_plan={is_json}")
        if plan:
            print(f"  headline: {plan.get('headline','')[:80]}")
            print(f"  has_fire: {'fire' in plan and plan['fire'] is not None}")
            print(f"  has_tax:  {'tax' in plan and plan['tax'] is not None}")
        else:
            print(f"  reply: {reply[:120]}")
        print()

print("=== SCENARIO 1: Tax only ===")
chat_session([
    "I have a salary of 50 LPA, help me manage my taxes",
    "I am 28 years old",
])

print("=== SCENARIO 2: Retirement ===")
chat_session([
    "I want to plan my retirement, I am 30 earning 15 lakhs",
    "Monthly expenses 40k, savings 5 lakhs, moderate risk",
])
