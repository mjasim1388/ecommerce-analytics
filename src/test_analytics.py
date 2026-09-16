import analytics as a

print("KPIs:")
print(a.top_kpis().to_string(index=False))

print("\nMonthly revenue (first 3 rows):")
print(a.monthly_revenue().head(3).to_string(index=False))

print("\nTop 5 products:")
print(a.top_products(5).to_string(index=False))

print("\nTop 5 states:")
print(a.revenue_by_state().head(5).to_string(index=False))

print("\nRetention (first 3 rows):")
print(a.retention().head(3).to_string(index=False))

print("\nRFM segments:")
print(a.rfm_segments().to_string(index=False))