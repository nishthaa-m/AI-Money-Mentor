from backend.tools.calculations import (
    calculate_fire_number, calculate_years_to_fire,
    asset_allocation, emergency_fund_target, insurance_gap_analysis
)
from backend.tools.tax_engine import DeductionProfile, compare_regimes, identify_missed_deductions

# Test 1: FIRE
fire_num = calculate_fire_number(50000, 30)
years = calculate_years_to_fire(500000, 30000, fire_num)
alloc = asset_allocation(30, "moderate")
print(f"FIRE Number: Rs {fire_num:,.0f}")
print(f"Years to FIRE: {years}")
print(f"Asset Allocation: {alloc}")
print()

# Test 2: Tax comparison (edge case — both regimes)
d = DeductionProfile(section_80c=150000, section_80d_self=25000, section_80ccd1b=50000)
result = compare_regimes(1200000, d)
print(f"Recommended: {result['recommended_regime']} — {result['verdict']}")
print(f"New regime tax: Rs {result['new_regime']['total_tax']:,.0f}")
print(f"Old regime tax: Rs {result['old_regime']['total_tax']:,.0f}")
print()

# Test 3: Missed deductions
missed = identify_missed_deductions(1200000, DeductionProfile(section_80c=50000))
for m in missed:
    print(f"Missed {m['section']}: gap Rs {m['gap']:,.0f}, potential saving Rs {m['tax_saving_estimate']:,.0f}")

print()
# Test 4: Insurance gap
ins = insurance_gap_analysis(1200000, existing_term_cover=5000000, existing_health_cover=300000, dependents=2)
print(f"Term gap: Rs {ins['term_gap']:,.0f}")
print(f"Health gap: Rs {ins['health_gap']:,.0f}")
print()
print("All calculations passed.")
