import sqlite3, pandas as pd

con = sqlite3.connect("data/company_data/Company_data.db")
df = pd.read_sql_query("SELECT * FROM monthly_kpis ORDER BY month", con, parse_dates=["month"])
con.close()

snap = df.loc[df["month"] == "2025-08-01", 
              ["new_customers","contribution_margin_pct","cost_to_serve"]].iloc[0].to_dict()
print(snap)

trend = df.tail(12)[["month","new_customers","contribution_margin_pct","cost_to_serve"]]
print(trend)