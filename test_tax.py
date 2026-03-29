from backend.tools.tax_engine import calculate_tax, compare_regimes, DeductionProfile

# Test 50 LPA
d = DeductionProfile()
new = calculate_tax(5_000_000, d, "new")
old = calculate_tax(5_000_000, d, "old")

print("=== 50 LPA NEW regime ===")
print(f"  Taxable income: {new['taxable_income']:,.0f}")
print(f"  Base tax:       {new['base_tax']:,.0f}")
print(f"  Surcharge:      {new['surcharge']:,.0f}")
print(f"  Cess:           {new['cess']:,.0f}")
print(f"  TOTAL TAX:      {new['total_tax']:,.0f}")
print(f"  Effective rate: {new['effective_rate_pct']}%")
print()
print("=== 50 LPA OLD regime (no deductions) ===")
print(f"  Taxable income: {old['taxable_income']:,.0f}")
print(f"  TOTAL TAX:      {old['total_tax']:,.0f}")
print(f"  Effective rate: {old['effective_rate_pct']}%")
print()

# Test 15 LPA (the common case)
new15 = calculate_tax(1_500_000, d, "new")
old15 = calculate_tax(1_500_000, d, "old")
print("=== 15 LPA NEW regime ===")
print(f"  TOTAL TAX: {new15['total_tax']:,.0f}  Effective: {new15['effective_rate_pct']}%")
print("=== 15 LPA OLD regime ===")
print(f"  TOTAL TAX: {old15['total_tax']:,.0f}  Effective: {old15['effective_rate_pct']}%")
