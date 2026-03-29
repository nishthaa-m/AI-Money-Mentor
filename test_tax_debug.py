"""Debug why 50 LPA shows ₹0 tax"""
from backend.tools.tax_engine import calculate_tax, DeductionProfile

# Simulate what the profiler extracts for "50 LPA"
# "50 LPA" = 50 lakhs per annum = 5,000,000
d = DeductionProfile()

r_new = calculate_tax(5_000_000, d, "new")
print(f"50 LPA (5000000) new: tax={r_new['total_tax']:,.0f}, taxable={r_new['taxable_income']:,.0f}")

# What if profiler extracted 600000 instead of 5000000?
r_wrong = calculate_tax(600_000, d, "new")
print(f"6 LPA (600000) new: tax={r_wrong['total_tax']:,.0f}")  # this would be 0

# What if "50 LPA" was parsed as 50*100000 = 5000000 or 50*12 monthly?
print(f"\nIf '50 LPA' was parsed as 50000: tax={calculate_tax(50000, d, 'new')['total_tax']:,.0f}")
print(f"If '50 LPA' was parsed as 500000: tax={calculate_tax(500_000, d, 'new')['total_tax']:,.0f}")
print(f"If '50 LPA' was parsed as 5000000: tax={calculate_tax(5_000_000, d, 'new')['total_tax']:,.0f}")
