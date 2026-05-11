import pandas as pd

# ── STEP 1 : LOAD & CLEAN ─────────────────────────────────────────────────────
df = pd.read_csv("audit_data.csv")

df['Country_Code'] = df['Country_Code'].str.strip().str.upper()
df['Pay_Date']     = pd.to_datetime(df['Pay_Date'], dayfirst=True)
df['Is_Outlier']   = df['Is_Outlier'].str.strip().str.upper() == 'YES'

print(f"Total Records Loaded : {len(df):,}")


# ── STEP 2 : FILTER BY STATUS ─────────────────────────────────────────────────
paid_df   = df[df['Status'] == 'Paid']
failed_df = df[df['Status'] == 'Failed']
# Pending and Withdrawn are excluded — no payment was made

print(f"Audit Scope          : {len(paid_df) + len(failed_df):,} records")
print(f"Excluded             : {len(df) - len(paid_df) - len(failed_df):,} records")


# ── STEP 3 : PAID BRANCH — OUTLIER ANALYSIS ───────────────────────────────────
outliers = paid_df[paid_df['Is_Outlier'] == True]

print(f"\n── Paid Branch ──")
print(f"Total Paid           : {len(paid_df):,}")
print(f"Outliers Flagged     : {len(outliers):,}  ({len(outliers)/len(paid_df)*100:.2f}%)")
print(f"Total Exposure (USD) : ${outliers['Variance_USD'].sum():,.2f}")

# Which country has the most errors?
country_risk = (paid_df.groupby('Country_Code')['Variance_USD']
                .sum()
                .sort_values(ascending=False))
print(f"\nVariance by Country :\n{country_risk.apply('${:,.2f}'.format)}")

# Which account type is most affected?
acct_risk = (outliers.groupby('Account_Type')['Variance_USD']
             .sum()
             .sort_values(ascending=False))
print(f"\nVariance by Account Type :\n{acct_risk.apply('${:,.2f}'.format)}")


# ── STEP 4 : FAILED BRANCH — ROOT CAUSE ANALYSIS ──────────────────────────────
print(f"\n── Failed Branch ──")
print(f"Total Failed         : {len(failed_df):,}")
print(f"Value Stuck          : ${failed_df['Expected_Net_USD'].sum():,.2f}")

# Why are transactions failing?
root_cause = (failed_df.groupby('Failure_Reason')['Txn_ID']
              .count()
              .sort_values(ascending=False))
print(f"\nRoot Cause Breakdown :\n{root_cause}")


# ── STEP 5 : SUMMARY ──────────────────────────────────────────────────────────
print(f"""
════════════════════════════════════════
  AUDIT SUMMARY
════════════════════════════════════════
  Highest Risk Country : {country_risk.idxmax()}
  Top Failure Reason   : {root_cause.idxmax()}
  Total Exposure       : ${outliers['Variance_USD'].sum():,.2f}
════════════════════════════════════════
""")
