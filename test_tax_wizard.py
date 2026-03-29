from dotenv import load_dotenv; load_dotenv()
import requests, json

payload = {
    "annual_income": 1800000,
    "basic_salary": 720000,
    "hra_received": 360000,
    "rent_paid": 480000,
    "metro_city": True,
    "section_80c_invested": 150000,
    "section_80ccd1b": 50000,
    "home_loan_interest": 40000,
    "age": 32,
    "tds_deducted": 180000,
}
r = requests.post("http://localhost:8000/tax/analyze", json=payload, timeout=10)
d = r.json()
s = d.get("summary", {})
print("Status:", r.status_code)
print(f"Recommended: {s.get('recommended_regime')}")
print(f"Tax: ₹{s.get('current_tax', 0):,.0f}")
print(f"Effective rate: {s.get('effective_rate')}%")
print(f"TDS gap: ₹{s.get('tds_gap', 0):,.0f}")
print(f"Max additional saving: ₹{s.get('max_additional_saving_possible', 0):,.0f}")
print(f"Steps (new): {len(d.get('tax_steps_new', {}).get('steps', []))}")
print(f"Instruments: {len(d.get('tax_instruments', []))}")
hra = d.get("hra_calculation", {})
if hra:
    print(f"HRA exempt: ₹{hra.get('hra_exempt', 0):,.0f}")
missed = d.get("missed_deductions", [])
print(f"Missed deductions: {len(missed)}")
for m in missed:
    print(f"  {m['section']}: save ₹{m['tax_saving_estimate']:,.0f}")
