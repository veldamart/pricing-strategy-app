import pandas as pd
import numpy as np
from scipy import stats

def run_master_competitive_pricing_engine(
    df_sold, 
    df_active, 
    subject_sqft, 
    sold_90_days, 
    under_contract, 
    active_count, 
    expired_count, 
    seasonality="Peak", 
    bridge_increment=25000
):
    """
    Unified Competitive Positioning Pricing Engine (Steps 1 - 4)
    """
    
    # --- STEP 1: HISTORICAL BASE PRICE ENGINE ---
    df_s = df_sold.copy()
    df_s['Price_Per_SqFt'] = df_s['Sold_Price'] / df_s['Finished_SqFt']
    
    # Outlier Removal (IQR)
    q1, q3 = df_s['Price_Per_SqFt'].quantile([0.25, 0.75])
    iqr = q3 - q1
    clean_solds = df_s[(df_s['Price_Per_SqFt'] >= q1 - 1.5 * iqr) & 
                        (df_s['Price_Per_SqFt'] <= q3 + 1.5 * iqr)]
    
    # OLS Linear Regression
    slope, intercept, r_val, _, _ = stats.linregress(clean_solds['Finished_SqFt'], clean_solds['Sold_Price'])
    base_price = (slope * subject_sqft) + intercept
    low_baseline = round((base_price * 0.95) / 10000) * 10000
    high_baseline = round((base_price * 1.05) / 10000) * 10000
    
    # --- STEP 2: MARKET DYNAMICS & POND ANALYTICS ---
    total_attempted = sold_90_days + active_count + expired_count
    odds_of_selling = (sold_90_days / total_attempted * 100) if total_attempted > 0 else 0.0
    
    season_mults = {"Peak": 1.15, "Transition": 1.0, "Off-Season": 0.85}
    proj_demand = sold_90_days * season_mults.get(seasonality, 1.0)
    opportunity_score = proj_demand - under_contract
    
    monthly_sales = sold_90_days / 3.0
    moi = (active_count / monthly_sales) if monthly_sales > 0 else 999.0
    
    if moi < 3.0:
        momentum_state = "Seller Advantage"
    elif 3.0 <= moi <= 5.0:
        momentum_state = "Balanced Market"
    else:
        momentum_state = "Buyer Advantage"

    # --- STEP 4: BRIDGE PRICING ENGINE ---
    lower_bridge = (base_price // bridge_increment) * bridge_increment
    upper_bridge = lower_bridge + bridge_increment
    
    if momentum_state == "Seller Advantage":
        rec_price = upper_bridge
        strat_name = "Aggressive Threshold Capture"
    elif momentum_state == "Buyer Advantage":
        rec_price = lower_bridge
        strat_name = "Defensive Value Anchor"
    else:
        rec_price = lower_bridge if abs(base_price - lower_bridge) < abs(base_price - upper_bridge) else upper_bridge
        strat_name = "Balanced Bridge Boundary"

    # --- STEP 3: COMPETITIVE POSITIONING MATRIX ---
    df_a = df_active.copy()
    subject_row = pd.DataFrame([{'Address': '*** SUBJECT ***', 'Finished_SqFt': subject_sqft, 'List_Price': rec_price}])
    comp_df = pd.concat([df_a, subject_row], ignore_index=True)
    
    med_price = comp_df['List_Price'].median()
    med_sqft = comp_df['Finished_SqFt'].median()
    
    if rec_price <= med_price and subject_sqft >= med_sqft:
        quadrant = "Advantage (High Size, Lower Price)"
    elif rec_price > med_price and subject_sqft >= med_sqft:
        quadrant = "Premium / High End (High Size, High Price)"
    elif rec_price <= med_price and subject_sqft < med_sqft:
        quadrant = "Entry Level / Compact (Low Size, Low Price)"
    else:
        quadrant = "Disadvantage (Low Size, High Price)"

    # --- CONSOLIDATED REPORT OUTPUT ---
    return {
        "Base_Price": base_price,
        "Baseline_Corridor": (low_baseline, high_baseline),
        "Odds_Of_Selling_Pct": round(odds_of_selling, 1),
        "Opportunity_Demand": round(opportunity_score, 1),
        "Months_Of_Inventory": round(moi, 2),
        "Momentum_State": momentum_state,
        "Recommended_List_Price": rec_price,
        "Pricing_Strategy": strat_name,
        "Positioning_Quadrant": quadrant,
        "Lot_Value_Intercept": intercept,
        "Building_Value_Slope": slope
    }

# ---------------------------------------------------------
# EXECUTION TEST
# ---------------------------------------------------------
mock_solds = pd.DataFrame({
    'Finished_SqFt': [1800, 2100, 2300, 2600, 2900, 3200, 2500],
    'Sold_Price': [420000, 475000, 510000, 565000, 615000, 680000, 200000]
})

mock_actives = pd.DataFrame({
    'Finished_SqFt': [2200, 2600, 2100, 2800, 2300],
    'List_Price': [520000, 580000, 545000, 620000, 510000]
})

report = run_master_competitive_pricing_engine(
    df_sold=mock_solds,
    df_active=mock_actives,
    subject_sqft=2450,
    sold_90_days=24,
    under_contract=8,
    active_count=12,
    expired_count=4,
    seasonality="Peak"
)

print("=== FINAL MASTER PRICING REPORT ===")
for key, value in report.items():
    if "Price" in key or "Value" in key or "Corridor" in key:
        print(f"{key:25}: {value}")
    else:
        print(f"{key:25}: {value}")