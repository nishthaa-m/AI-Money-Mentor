from dotenv import load_dotenv; load_dotenv()
import requests, json

BASE = "http://localhost:8000"

# Test 1: 50 LPA should give ~₹11L tax, not ₹0
sid = requests.post(f"{BASE}/session/new").json()["session_id"]
turns = [
    "I have salary of 50 LPA, help me manage my taxes",
    "I am 28 years old",
]
for msg in turns:
    r = requests.post(f"{BASE}/chat", json={"session_id": sid, "message": msg}, timeout=60)
    d = r.json()
    reply = d.get("reply", "")
    is_json = reply.strip().startswith("{")
    if is_json:
        try:
            p = json.loads(reply[reply.index("{"):reply.rindex("}")+1])
            tax = p.get("tax", {})
            print(f"50 LPA result:")
            print(f"  their_tax:      ₹{tax.get('their_tax', 0):,.0f}  (expected ~₹11L)")
            print(f"  effective_rate: {tax.get('effective_rate', 0)}%  (expected ~22%)")
            print(f"  regime:         {tax.get('recommended_regime')}")
            print(f"  headline:       {p.get('headline','')[:80]}")
        except Exception as e:
            print(f"Parse error: {e}\n{reply[:200]}")
    else:
        print(f"  followup: {reply[:100]}")

print()
# Test 2: 15 LPA
sid2 = requests.post(f"{BASE}/session/new").json()["session_id"]
turns2 = ["I earn 15 lakhs per year, 30 years old, help with taxes"]
for msg in turns2:
    r = requests.post(f"{BASE}/chat", json={"session_id": sid2, "message": msg}, timeout=60)
    d = r.json()
    reply = d.get("reply", "")
    is_json = reply.strip().startswith("{")
    if is_json:
        try:
            p = json.loads(reply[reply.index("{"):reply.rindex("}")+1])
            tax = p.get("tax", {})
            print(f"15 LPA result:")
            print(f"  their_tax:      ₹{tax.get('their_tax', 0):,.0f}  (expected ~₹97,500)")
            print(f"  effective_rate: {tax.get('effective_rate', 0)}%  (expected ~6.5%)")
        except Exception as e:
            print(f"Parse error: {e}")
    else:
        print(f"  followup: {reply[:100]}")
