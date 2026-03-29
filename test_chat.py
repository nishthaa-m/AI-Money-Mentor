from dotenv import load_dotenv; load_dotenv()
import requests, json

r = requests.post('http://localhost:8000/session/new')
sid = r.json()['session_id']
print("Session:", sid)

turns = [
    'I want to plan my retirement. I am 30, earning 15 lakhs per year',
    'My monthly expenses are around 40000. I have 5 lakhs saved so far',
    'Moderate risk, no dependents',
]

for i, msg in enumerate(turns):
    r = requests.post('http://localhost:8000/chat',
        json={'session_id': sid, 'message': msg}, timeout=60)
    d = r.json()
    print(f"Turn {i+1} | scenario={d.get('scenario')} | complete={d.get('profile_complete')} | calcs={bool(d.get('calculations'))}")
    print("Reply:", d.get('reply','')[:300])
    print()
