# Corporate Action Audit Pipeline
## Step 1 — EDA & Data Quality Control
**Project:** Enterprise Corporate Action Audit & Reconciliation Pipeline  
**Tech Stack:** Python (Pandas), MySQL, Power BI  
**Author:** [Lalit Pratap Singh]
---
## 0. Setup — Import Libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

print('Libraries loaded successfully')
---
## 1. Load All 5 Datasets

dim_accounts   = pd.read_csv('dim_accounts.csv')
dim_events     = pd.read_csv('dim_events.csv')
fact_payouts   = pd.read_csv('fact_payouts.csv')
ref_fx_rates   = pd.read_csv('ref_fx_rates.csv')
ref_tax_rules  = pd.read_csv('ref_tax_rules.csv')

print('All 5 datasets loaded')
print(f'  dim_accounts   : {dim_accounts.shape}')
print(f'  dim_events     : {dim_events.shape}')
print(f'  fact_payouts   : {fact_payouts.shape}')
print(f'  ref_fx_rates   : {ref_fx_rates.shape}')
print(f'  ref_tax_rules  : {ref_tax_rules.shape}')
---
## 2. Part A — Basic EDA (Understand the Data)

### 2.1 dim_accounts — Client Master Data
print('=== dim_accounts ===')
print(f'Shape: {dim_accounts.shape}')
print(f'\nFirst 5 rows:')
display(dim_accounts.head())
print(f'\nColumn Data Types:')
print(dim_accounts.dtypes)
print(f'\nUnique values per column:')
for col in dim_accounts.columns:
    print(f'  {col}: {dim_accounts[col].nunique()} unique values')
  
# Account_Type distribution
print('Account_Type distribution:')
print(dim_accounts['Account_Type'].value_counts())
print('\nCountry_Code distribution:')
print(dim_accounts['Country_Code'].value_counts())
print('\nSovereign_Exemption_Flag distribution:')
print(dim_accounts['Sovereign_Exemption_Flag'].value_counts(dropna=False))

### 2.2 dim_events — Corporate Action Events
print('=== dim_events ===')
print(f'Shape: {dim_events.shape}')
display(dim_events.head())
print(f'\nEvent_Type distribution:')
print(dim_events['Event_Type'].value_counts())
print(f'\nMandatory_Flag distribution:')
print(dim_events['Mandatory_Flag'].value_counts())
print(f'\nCurrency distribution:')
print(dim_events['Currency'].value_counts())
print(f'\nRate_Per_Share stats:')
print(dim_events['Rate_Per_Share'].describe())

### 2.3 fact_payouts — Transaction Records 
print('=== fact_payouts ===')
print(f'Shape: {fact_payouts.shape}')
display(fact_payouts.head())
print(f'\nStatus distribution:')
print(fact_payouts['Status'].value_counts())
print(f'\nFailure_Reason distribution:')
print(fact_payouts['Failure_Reason'].value_counts(dropna=False))
print(f'\nSystem_Net_Paid_USD stats:')
print(fact_payouts['System_Net_Paid_USD'].describe())
# Status breakdown as percentage
status_pct = fact_payouts['Status'].value_counts(normalize=True).mul(100).round(2)
print('Status breakdown (%):')
print(status_pct)

# Visualize
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

status_pct.plot(kind='bar', ax=axes[0], color=['#2ecc71','#e74c3c','#f39c12','#95a5a6'])
axes[0].set_title('Transaction Status Distribution (%)')
axes[0].set_xlabel('Status')
axes[0].set_ylabel('Percentage')
axes[0].tick_params(axis='x', rotation=0)

failure_data = fact_payouts['Failure_Reason'].value_counts()
failure_data.plot(kind='bar', ax=axes[1], color='#e74c3c')
axes[1].set_title('Failure Reason Distribution')
axes[1].set_xlabel('Failure Reason')
axes[1].set_ylabel('Count')
axes[1].tick_params(axis='x', rotation=0)

plt.tight_layout()
plt.savefig('eda_status_distribution.png', dpi=150, bbox_inches='tight')
plt.show()
print('Chart saved as eda_status_distribution.png')

### 2.4 ref_fx_rates — Foreign Exchange Rates
print('=== ref_fx_rates ===')
print(f'Shape: {ref_fx_rates.shape}')
display(ref_fx_rates.head())
print(f'\nSource distribution:')
print(ref_fx_rates['Source'].value_counts())
print(f'\nCurrency distribution:')
print(ref_fx_rates['Currency'].value_counts())
print(f'\nDate range:')
print(f'  From: {ref_fx_rates["Rate_Date"].min()}')
print(f'  To:   {ref_fx_rates["Rate_Date"].max()}')

### 2.5 ref_tax_rules — Tax Withholding Rules
print('=== ref_tax_rules ===')
print(f'Shape: {ref_tax_rules.shape}')
display(ref_tax_rules)
print(f'\nCountries covered: {ref_tax_rules["Country_Code"].unique()}')
print(f'Account types covered: {ref_tax_rules["Account_Type"].unique()}')
---
## 3. Part B — Data Quality Checks (Cleaning)

### 3.1 Null Value Check — All Tables
tables = {
    'dim_accounts' : dim_accounts,
    'dim_events'   : dim_events,
    'fact_payouts' : fact_payouts,
    'ref_fx_rates' : ref_fx_rates,
    'ref_tax_rules': ref_tax_rules
}

print('=== NULL VALUE REPORT ===')
for name, df in tables.items():
    null_cols = df.isnull().sum()
    null_cols = null_cols[null_cols > 0]
    if len(null_cols) > 0:
        print(f'\n⚠️  {name}:')
        for col, cnt in null_cols.items():
            pct = round(cnt / len(df) * 100, 2)
            print(f'   {col}: {cnt} nulls ({pct}%)')
    else:
        print(f'\n {name}: No nulls found')
### 3.2 Duplicate Row Check
print('=== DUPLICATE ROWS CHECK ===')
for name, df in tables.items():
    dups = df.duplicated().sum()
    status = '⚠️ ' if dups > 0 else '✅'
    print(f'{status} {name}: {dups} duplicate rows')

# Also check for duplicate primary keys
print('\n=== DUPLICATE PRIMARY KEY CHECK ===')
pk_checks = {
    'dim_accounts (Account_ID)' : dim_accounts['Account_ID'],
    'dim_events (Event_ID)'     : dim_events['Event_ID'],
    'fact_payouts (Txn_ID)'     : fact_payouts['Txn_ID'],
}
for name, col in pk_checks.items():
    dups = col.duplicated().sum()
    status = '⚠️ ' if dups > 0 else '✅'
    print(f'{status} {name}: {dups} duplicate keys')
### 3.3 Fix 1 — Standardize Date Columns
# Convert all date columns to datetime format
date_cols_events = ['Ex_Date', 'Record_Date', 'Pay_Date']
for col in date_cols_events:
    dim_events[col] = pd.to_datetime(dim_events[col])

fact_payouts['Settlement_Date'] = pd.to_datetime(fact_payouts['Settlement_Date'])
ref_fx_rates['Rate_Date'] = pd.to_datetime(ref_fx_rates['Rate_Date'])

print('✅ Date columns converted to datetime format')
print('\ndim_events date dtypes:')
print(dim_events[date_cols_events].dtypes)
### 3.4 Fix 2 — Standardize Text Columns (Case Issues)
# PROBLEM FOUND: 'Dividend' and 'DIVIDEND' are same but different case
print('BEFORE - Event_Type unique values:')
print(dim_events['Event_Type'].value_counts())

dim_events['Event_Type'] = dim_events['Event_Type'].str.strip().str.title()

print('\nAFTER - Event_Type unique values (standardized):')
print(dim_events['Event_Type'].value_counts())
# PROBLEM FOUND: 'retail' and 'Retail' in Account_Type
print('BEFORE - Account_Type unique values:')
print(dim_accounts['Account_Type'].value_counts())

dim_accounts['Account_Type'] = dim_accounts['Account_Type'].str.strip().str.title()

print('\nAFTER - Account_Type unique values (standardized):')
print(dim_accounts['Account_Type'].value_counts())
### 3.5 Fix 3 — Handle Nulls in Sovereign_Exemption_Flag
# 261 nulls found in Sovereign_Exemption_Flag
# Business Rule: If flag is NULL, treat as 'N' (Not Exempt) — safe default
print('BEFORE - Sovereign_Exemption_Flag nulls:', dim_accounts['Sovereign_Exemption_Flag'].isnull().sum())

dim_accounts['Sovereign_Exemption_Flag'] = dim_accounts['Sovereign_Exemption_Flag'].fillna('N')

print('AFTER  - Sovereign_Exemption_Flag nulls:', dim_accounts['Sovereign_Exemption_Flag'].isnull().sum())
print('Distribution:', dim_accounts['Sovereign_Exemption_Flag'].value_counts().to_dict())
print('\n✅ Business Rule Applied: NULL Sovereign Flag = Not Exempt (N)')
---
## 4. Part C — Business-Specific Quality Checks
### 4.1 Referential Integrity Check
print('=== REFERENTIAL INTEGRITY CHECK ===')

# Check 1: Every Event_ID in fact_payouts exists in dim_events?
valid_event_ids = set(dim_events['Event_ID'])
orphan_events = fact_payouts[~fact_payouts['Event_ID'].isin(valid_event_ids)]
print(f'\n1. Orphan Event_IDs in fact_payouts: {len(orphan_events)}')
if len(orphan_events) > 0:
    print(f'   ⚠️  These transactions reference events that do not exist!')
else:
    print(f'   ✅ All Event_IDs are valid')

# Check 2: Every Account_ID in fact_payouts exists in dim_accounts?
valid_account_ids = set(dim_accounts['Account_ID'])
orphan_accounts = fact_payouts[~fact_payouts['Account_ID'].isin(valid_account_ids)]
print(f'\n2. Orphan Account_IDs in fact_payouts: {len(orphan_accounts)}')
if len(orphan_accounts) > 0:
    print(f'   ⚠️  These transactions reference accounts that do not exist!')
else:
    print(f'   ✅ All Account_IDs are valid')

# Check 3: Every Currency in dim_events has FX rate?
event_currencies = set(dim_events['Currency'].unique())
fx_currencies = set(ref_fx_rates['Currency'].unique())
missing_fx = event_currencies - fx_currencies
print(f'\n3. Currencies in dim_events with no FX rate: {missing_fx}')
if missing_fx:
    print(f'   ⚠️  These currencies have no exchange rate — audit will fail for them!')
else:
    print(f'   ✅ All event currencies have FX rates')
### 4.2 Stale FX Rate Detection (48-Hour Rule)
# Banking Rule: FX Rate must not be older than 48 hours from Pay_Date
# If Rate_Date < Pay_Date - 2 days → Stale Rate = HIGH RISK

# Merge events with fx rates on currency
events_with_fx = dim_events.merge(
    ref_fx_rates[['Currency', 'Rate_Date']].drop_duplicates(),
    on='Currency',
    how='left'
)

# Calculate difference in hours
events_with_fx['Rate_Date'] = pd.to_datetime(events_with_fx['Rate_Date'])
events_with_fx['Pay_Date']  = pd.to_datetime(events_with_fx['Pay_Date'])
events_with_fx['Rate_Age_Hours'] = (
    events_with_fx['Pay_Date'] - events_with_fx['Rate_Date']
).dt.total_seconds() / 3600

# Flag stale rates
stale_rates = events_with_fx[events_with_fx['Rate_Age_Hours'] > 48]
stale_pct = round(len(stale_rates) / len(events_with_fx) * 100, 2)

print(f'=== STALE FX RATE CHECK (>48 hours) ===')
print(f'Total event-rate combinations checked : {len(events_with_fx)}')
print(f'Stale rate records flagged            : {len(stale_rates)} ({stale_pct}%)')
if len(stale_rates) > 0:
    print(f'\n⚠️  HIGH RISK: These events used outdated FX rates!')
    print(f'   Currencies affected: {stale_rates["Currency"].unique()}')
    print(f'   Max rate age: {stale_rates["Rate_Age_Hours"].max():.0f} hours')
else:
    print('✅ All FX rates are fresh')
### 4.3 Negative Value Check
print('=== NEGATIVE VALUE CHECK ===')

# Position_Qty should never be negative
neg_position = fact_payouts[fact_payouts['Position_Qty'] < 0]
print(f'Negative Position_Qty records: {len(neg_position)}')
if len(neg_position) > 0:
    print('⚠️  Found negative positions — possible data entry error!')
else:
    print('✅ No negative positions')

# Rate_Per_Share should never be negative
neg_rate = dim_events[dim_events['Rate_Per_Share'] < 0]
print(f'\nNegative Rate_Per_Share records: {len(neg_rate)}')
if len(neg_rate) > 0:
    print('⚠️  Found negative rates!')
else:
    print('✅ No negative rates')

# System_Net_Paid_USD should never be negative
neg_paid = fact_payouts[fact_payouts['System_Net_Paid_USD'] < 0]
print(f'\nNegative System_Net_Paid_USD records: {len(neg_paid)}')
if len(neg_paid) > 0:
    print('⚠️  Found negative payment amounts!')
else:
    print('✅ No negative payment amounts')
### 4.4 FX Rate Deduplication Check (Multiple Sources)
# Problem: Same currency on same date has rates from Bloomberg, Reuters, Internal
# We need to pick ONE authoritative source per currency per date

dup_fx = ref_fx_rates.groupby(['Currency', 'Rate_Date']).size().reset_index(name='count')
multi_source = dup_fx[dup_fx['count'] > 1]

print(f'=== FX RATE DUPLICATE SOURCE CHECK ===')
print(f'Currency+Date combos with multiple sources: {len(multi_source)}')

if len(multi_source) > 0:
    print(f'\n⚠️  Multiple sources found for same currency/date!')
    print(f'Sources present: {ref_fx_rates["Source"].unique()}')
    print(f'\nSource priority rule applied:')
    print('  Bloomberg (Priority 1) > Reuters (Priority 2) > Internal (Priority 3)')

# Apply source priority — this is the "Golden Source" logic
source_priority = {'Bloomberg': 1, 'Reuters': 2, 'Internal': 3}
ref_fx_rates['Source_Priority'] = ref_fx_rates['Source'].map(source_priority)

# Keep only highest priority (lowest number) per currency per date
ref_fx_rates_clean = (
    ref_fx_rates
    .sort_values('Source_Priority')
    .drop_duplicates(subset=['Currency', 'Rate_Date'], keep='first')
    .drop(columns='Source_Priority')
    .reset_index(drop=True)
)

print(f'\nBEFORE deduplication: {len(ref_fx_rates)} rows')
print(f'AFTER  deduplication: {len(ref_fx_rates_clean)} rows')
print('✅ Golden Source FX rates selected (Bloomberg > Reuters > Internal)')
---
## 5. Final Summary — Cleaned Datasets
print('=' * 60)
print('        STEP 1 — DATA QUALITY SUMMARY REPORT')
print('=' * 60)

issues_found = [
    ('dim_accounts',  'Sovereign_Exemption_Flag had 261 NULLs → Filled with N'),
    ('dim_accounts',  'Account_Type had mixed case (retail/Retail) → Title cased'),
    ('dim_events',    'Event_Type had mixed case (DIVIDEND/Dividend) → Title cased'),
    ('ref_fx_rates',  'Multiple sources per currency/date → Bloomberg chosen as Golden Source'),
]

print('\n🔧 Issues Found & Fixed:')
for table, issue in issues_found:
    print(f'   [{table}] {issue}')

print('\n✅ Checks Passed:')
print('   No duplicate primary keys')
print('   No orphan Event_IDs or Account_IDs')
print('   No negative Position_Qty or Rate_Per_Share')
print('   All event currencies have FX rates')

print('\n📦 Clean Datasets Ready for Step 2 (MySQL):')
print(f'   dim_accounts_clean   : {dim_accounts.shape}')
print(f'   dim_events_clean     : {dim_events.shape}')
print(f'   fact_payouts         : {fact_payouts.shape}')
print(f'   ref_fx_rates_clean   : {ref_fx_rates_clean.shape}')
print(f'   ref_tax_rules        : {ref_tax_rules.shape}')
---
## 6. Export Cleaned CSVs (for MySQL Import)
# Save cleaned files — these will be imported into MySQL Workbench
dim_accounts.to_csv('dim_accounts_clean.csv', index=False)
dim_events.to_csv('dim_events_clean.csv', index=False)
fact_payouts.to_csv('fact_payouts_clean.csv', index=False)
ref_fx_rates_clean.to_csv('ref_fx_rates_clean.csv', index=False)
ref_tax_rules.to_csv('ref_tax_rules_clean.csv', index=False)

print('✅ All 5 cleaned CSVs exported!')
print('Next Step: Import these into MySQL Workbench for Step 2 (Business Logic)')
