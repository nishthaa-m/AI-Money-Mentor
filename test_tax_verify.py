"""
Manual verification against ClearTax / IT dept calculator for FY2024-25
Sources:
- https://incometaxindia.gov.in/Pages/tools/tax-calculator.aspx
- https://cleartax.in/s/income-tax-calculator
"""
from backend.tools.tax_engine import calculate_tax, compare_regimes, DeductionProfile

print("=== VERIFICATION: FY 2024-25 ===\n")

# Case 1: 12 LPA, new regime
# Expected: taxable = 12L - 75k = 11.25L
# 0-3L: 0, 3-7L: 20000, 7-10L: 30000, 10-11.25L: 18750 = 68750
# Cess: 68750 * 4% = 2750 → Total = 71500
r = calculate_tax(1_200_000, DeductionProfile(), "new")
print(f"12 LPA new regime: ₹{r['total_tax']:,.0f} (expected ~₹71,500) ✓" if abs(r['total_tax'] - 71500) < 100 else f"12 LPA new regime: ₹{r['total_tax']:,.0f} MISMATCH expected ₹71,500")

# Case 2: 7.75 LPA, new regime — should be ZERO (rebate 87A)
# Taxable = 7.75L - 75k = 7L exactly → full rebate
r2 = calculate_tax(775_000, DeductionProfile(), "new")
print(f"7.75 LPA new regime: ₹{r2['total_tax']:,.0f} (expected ₹0) {'✓' if r2['total_tax'] == 0 else 'MISMATCH'}")

# Case 3: 10 LPA, new regime
# Taxable = 10L - 75k = 9.25L
# 0-3L:0, 3-7L:20000, 7-9.25L:22500 = 42500 + cess 1700 = 44200
r3 = calculate_tax(1_000_000, DeductionProfile(), "new")
print(f"10 LPA new regime: ₹{r3['total_tax']:,.0f} (expected ~₹44,200) {'✓' if abs(r3['total_tax'] - 44200) < 200 else 'MISMATCH'}")

# Case 4: 15 LPA, new regime
# Taxable = 15L - 75k = 14.25L
# 0-3L:0, 3-7L:20000, 7-10L:30000, 10-12L:30000, 12-14.25L:45000 = 125000
# Cess: 5000 → Total = 130000
r4 = calculate_tax(1_500_000, DeductionProfile(), "new")
print(f"15 LPA new regime: ₹{r4['total_tax']:,.0f} (expected ~₹1,30,000) {'✓' if abs(r4['total_tax'] - 130000) < 500 else 'MISMATCH'}")

# Case 5: 50 LPA, new regime
# Taxable = 50L - 75k = 49.25L
# 0-3L:0, 3-7L:20000, 7-10L:30000, 10-12L:30000, 12-15L:60000, 15-49.25L:1027500 = 1167500
# No surcharge (< 50L), Cess: 46700 → Total = 1214200
r5 = calculate_tax(5_000_000, DeductionProfile(), "new")
print(f"50 LPA new regime: ₹{r5['total_tax']:,.0f} (expected ~₹12,14,200) {'✓' if abs(r5['total_tax'] - 1214200) < 1000 else 'MISMATCH'}")

print("\n=== OLD REGIME with full deductions ===")
# 15 LPA, old regime, full 80C+80CCD+80D
d_full = DeductionProfile(section_80c=150000, section_80ccd1b=50000, section_80d_self=25000)
r6 = calculate_tax(1_500_000, d_full, "old")
# Taxable = 15L - 50k(std) - 1.5L(80C) - 50k(NPS) - 25k(80D) = 15L - 2.75L = 12.25L
# 0-2.5L:0, 2.5-5L:12500, 5-10L:100000, 10-12.25L:45000 = 157500
# Cess: 6300 → Total = 163800
print(f"15 LPA old regime (full deductions): ₹{r6['total_tax']:,.0f} (expected ~₹1,63,800)")
print(f"  Taxable income: ₹{r6['taxable_income']:,.0f}")
