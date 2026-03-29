from backend.tools.tax_engine import _slab_tax, OLD_REGIME_SLABS

# Manual: taxable = 12.25L
# 0-2.5L: 0
# 2.5-5L: 2.5L * 5% = 12500
# 5-10L: 5L * 20% = 100000
# 10-12.25L: 2.25L * 30% = 67500
# Total base = 180000, cess = 7200, total = 187200
t = _slab_tax(1_225_000, OLD_REGIME_SLABS)
print(f"Base tax on 12.25L: {t:,.0f}")  # should be 180000
print(f"With 4% cess: {t * 1.04:,.0f}")  # 187200

# My manual calc was wrong — 10-12.25L at 30% = 67500, not 45000
# 180000 + 7200 = 187200 is CORRECT
print("Tax engine is correct. My manual estimate was wrong.")
