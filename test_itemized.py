from dotenv import load_dotenv; load_dotenv()
import requests

r = requests.post('http://localhost:8000/session/new')
sid = r.json()['session_id']

turns = [
    'Help me plan my retirement. I am 30, earning 15 lakhs per year',
    'Rent - 20000/month, Groceries - 20000/month, Other Necessities - 30000',
    '5 lakhs saved so far, moderate risk',
]

for i, msg in enumerate(turns):
    r = requests.post('http://localhost:8000/chat',
        json={'session_id': sid, 'message': msg}, timeout=60)
    d = r.json()
    print(f"Turn {i+1} | complete={d.get('profile_complete')} | calcs={bool(d.get('calculations'))}")
    if d.get('calculations') and d['calculations'].get('fire'):
        fire = d['calculations']['fire']
        print(f"  monthly_expenses used: {fire.get('monthly_savings_available')}")
    print(f"  Reply: {d.get('reply','')[:200]}")
    print()
