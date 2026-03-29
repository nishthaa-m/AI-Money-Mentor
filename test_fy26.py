"""
FY2025-26 Tax Verification
Key change: New regime rebate 87A raised to ₹12L taxable (₹12.75L gross)
"""
from backend.tools.tax_engine import calculate_tax, compare_regimes, DeductionProfile

d = DeductionProfile()
print("=== FY2025-26 NEW REGIME ===")

cases = [
    (700_000,   "7L",   0),          # below 12L taxable → zero tax
    (1_000_000, "10L",  0),          # taxable = 9.25L → zero (rebate)
    (1_275_000, "12.75L", 0),        # taxable = 12L exactly → zero (rebate limit)
    (1_300_000, "13L",  None),       # taxable = 12.25L → tax kicks in
    (1_500_000, "15L",  None),
    (2_000_000, "20L",  None),
    (5_000_000, "50L",  None),
]

for income, label, expected in cases:
    r = calculate_tax(income, d, "new")
    match = ""
    if expected is not None:
        match = "✓" if abs(r["total_tax"] - expected) < 100 else "CHECK"
    print(f"  {label:8s} → tax={r['total_tax']:>12,.0f}  taxable={r['taxable_income']:>12,.0f}  eff={r['effective_rate_pct']:5.1f}%  {match}")

print()
print("=== ZERO TAX THRESHOLD ===")
# Should be zero up to 12.75L gross (12L taxable after 75k std ded)
r1 = calculate_tax(1_275_000, d, "new")
r2 = calculate_tax(1_276_000, d, "new")
print(f"  12.75L gross: tax = ₹{r1['total_tax']:,.0f}  (should be 0)")
print(f"  12.76L gross: tax = ₹{r2['total_tax']:,.0f}  (should be > 0)")

print()
print("=== OLD vs NEW COMPARISON ===")
d_full = DeductionProfile(section_80c=150000, section_80ccd1b=50000, section_80d_self=25000)
for income, label in [(1_500_000, "15L"), (2_000_000, "20L"), (5_000_000, "50L")]:
    c = compare_regimes(income, d_full)
    print(f"  {label}: new=₹{c['new_regime']['total_tax']:>10,.0f}  old=₹{c['old_regime']['total_tax']:>10,.0f}  → {c['recommended_regime']} saves ₹{c['tax_saving_with_recommended']:,.0f}")
