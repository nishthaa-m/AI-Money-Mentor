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
    calcs = d.get("calculations") or {}
    ls = calcs.get("literacy_score", {})
    if ls:
        print(f"Literacy: before={ls.get('before')} after={ls.get('after')} improvement={ls.get('improvement')}")
        print(f"  Level: {ls.get('level')}")
        dims = ls.get("dimensions", {})
        for k, v in dims.items():
            print(f"  {k}: {v['score']}/{v['max']}")
