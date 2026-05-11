-- ================================================
-- Corporate Action Audit & Reconciliation Pipeline
-- FINAL Audit Query — 5% Threshold
-- ================================================

USE corporate_action_audit;

WITH 

CTE1_Golden_FX AS (
    SELECT
        Currency, Rate_Date, USD_Exchange_Rate, Source,
        ROW_NUMBER() OVER (
            PARTITION BY Currency, Rate_Date
            ORDER BY
                CASE Source
                    WHEN 'Bloomberg' THEN 1
                    WHEN 'Reuters'   THEN 2
                    WHEN 'Internal'  THEN 3
                END
        ) AS rn
    FROM ref_fx_rates
),

CTE2_Base_Join AS (
    SELECT
        fp.Txn_ID, fp.Position_Qty, fp.Status,
        fp.System_Net_Paid_USD, fp.Failure_Reason,
        de.Event_ID, de.Event_Type, de.Currency,
        de.Rate_Per_Share, de.Pay_Date, de.Market_SLA_Hours,
        da.Account_ID, da.Account_Type, da.Country_Code,
        da.Sovereign_Exemption_Flag,
        fx.USD_Exchange_Rate
    FROM fact_payouts fp
    JOIN dim_events   de ON fp.Event_ID   = de.Event_ID
    JOIN dim_accounts da ON fp.Account_ID = da.Account_ID
    LEFT JOIN CTE1_Golden_FX fx
        ON  de.Currency = fx.Currency
        AND de.Pay_Date = fx.Rate_Date
        AND fx.rn       = 1
),

CTE3_Tax_Applied AS (
    SELECT
        b.*,
        CASE
            WHEN b.Sovereign_Exemption_Flag = 'Y' THEN 0
            ELSE COALESCE(tr.Withholding_Tax_Rate, 0)
        END AS Applied_Tax_Rate,
        ROUND(b.Position_Qty * b.Rate_Per_Share, 6) AS Gross_Amount_Local,
        CASE
            WHEN b.Sovereign_Exemption_Flag = 'Y' THEN 0
            ELSE ROUND(COALESCE(tr.Withholding_Tax_Rate, 0) * (b.Position_Qty * b.Rate_Per_Share), 6)
        END AS Tax_Amount_Local
    FROM CTE2_Base_Join b
    LEFT JOIN ref_tax_rules tr
        ON  b.Country_Code = tr.Country_Code
        AND b.Account_Type = tr.Account_Type
),

CTE4_Expected_USD AS (
    SELECT
        t.*,
        ROUND(Gross_Amount_Local - Tax_Amount_Local, 6)                                    AS Net_Amount_Local,
        ROUND((Gross_Amount_Local - Tax_Amount_Local) * COALESCE(t.USD_Exchange_Rate, 1), 4) AS Expected_Net_USD
    FROM CTE3_Tax_Applied t
),

CTE5_Variance AS (
    SELECT
        e.*,
        ROUND(ABS(e.System_Net_Paid_USD - e.Expected_Net_USD), 4) AS Variance_USD,
        ROUND(ABS(e.System_Net_Paid_USD - e.Expected_Net_USD) / NULLIF(e.Expected_Net_USD, 0) * 100, 6) AS Variance_Pct,
        CASE
            WHEN ABS(e.System_Net_Paid_USD - e.Expected_Net_USD)
                 / NULLIF(e.Expected_Net_USD, 0) * 100 > 5
            THEN 'YES'
            ELSE 'NO'
        END AS Is_Outlier
    FROM CTE4_Expected_USD e
)

-- Final Output
SELECT
    Txn_ID,
    Event_Type,
    Country_Code,
    Account_Type,
    Sovereign_Exemption_Flag,
    Currency,
    Position_Qty,
    Rate_Per_Share,
    USD_Exchange_Rate,
    Applied_Tax_Rate,
    Gross_Amount_Local,
    Tax_Amount_Local,
    Net_Amount_Local,
    Expected_Net_USD,
    System_Net_Paid_USD,
    Variance_USD,
    Variance_Pct,
    Is_Outlier,
    Failure_Reason,
    Status,
    Pay_Date,
    Market_SLA_Hours
FROM CTE5_Variance
ORDER BY Variance_USD DESC;
