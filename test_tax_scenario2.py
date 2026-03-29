from backend.tools.tax_engine import DeductionProfile, compare_regimes, calculate_tax_with_steps

# Judge scenario 2: ₹18L base, ₹3.6L HRA, ₹1.5L 80C, ₹50K NPS, ₹40K home loan interest
# HRA exempt: min(3.6L, 50%*basic, rent-10%*basic)
# Assume basic = 40% of 18L = 7.2L, rent = 4L (typical)
# HRA exempt = min(3.6L, 3.6L, 4L - 0.72L) = min(3.6L, 3.6L, 3.28L) = 3.28L

d = DeductionProfile(
    section_80c=150_000,
    section_80ccd1b=50_000,
    hra_exempt=328_000,   # computed HRA exemption
    home_loan_interest=40_000,
    age=32,
)

result = compare_regimes(1_800_000, d)
print(f"New regime: ₹{result['new_regime']['total_tax']:,.0f} ({result['new_regime']['effective_rate_pct']}%)")
print(f"Old regime: ₹{result['old_regime']['total_tax']:,.0f} ({result['old_regime']['effective_rate_pct']}%)")
print(f"Recommended: {result['recommended_regime']}")
print(f"Saving: ₹{result['tax_saving_with_recommended']:,.0f}")
print()

# Step by step for old regime
steps = calculate_tax_with_steps(1_800_000, d, "old")
print("=== OLD REGIME STEPS ===")
for s in steps["steps"]:
    sign = "-" if s["amount"] < 0 else " "
    print(f"  Step {s['step']}: {s['label']:40s} {sign}₹{abs(s['amount']):>12,.0f}  {s['note'][:50]}")
