import pandas as pd

def calculate_market_dynamics_engine(sold_90_days, under_contract, active, expired_withdrawn, seasonality="Peak"):
    """
    Step 2: Market Dynamics & Pond Analytics
    
    Parameters:
    - sold_90_days: Int, properties sold in the last 90 days
    - under_contract: Int, active listings currently pending/under contract
    - active: Int, current active listings on market
    - expired_withdrawn: Int, listings that failed to sell in the last 90 days
    - seasonality: Str, 'Peak', 'Off-Season', or 'Transition'
    
    Returns:
    - Dict containing Desirability (Odds of Selling), Opportunity Score, Velocity, and Market Momentum State
    """
    
    # 1. Desirability Metric (Odds of Selling %)
    total_attempted_sales = sold_90_days + active + expired_withdrawn
    odds_of_selling = (sold_90_days / total_attempted_sales * 100) if total_attempted_sales > 0 else 0.0
    
    # 2. Opportunity Score (Projected 90-Day Unsold Demand)
    # Applies seasonal demand multiplier to 90-day sales projection
    seasonality_multipliers = {"Peak": 1.15, "Transition": 1.0, "Off-Season": 0.85}
    projected_demand = sold_90_days * seasonality_multipliers.get(seasonality, 1.0)
    
    opportunity_score = projected_demand - under_contract
    
    # 3. Market Momentum Determination
    # Based on Months of Inventory (MOI) = Active / Monthly Sales Rate
    monthly_sales_rate = sold_90_days / 3.0
    months_of_inventory = (active / monthly_sales_rate) if monthly_sales_rate > 0 else 999.0
    
    if months_of_inventory < 3.0:
        momentum_state = "Seller Advantage"
        target_pricing_strategy = "Top of Baseline Range (Aggressive)"
    elif 3.0 <= months_of_inventory <= 5.0:
        momentum_state = "Balanced Market"
        target_pricing_strategy = "Center of Baseline Range (Neutral)"
    else:
        momentum_state = "Buyer Advantage"
        target_pricing_strategy = "Bottom of Baseline Range (Defensive)"
        
    return {
        "odds_of_selling_pct": round(odds_of_selling, 1),
        "opportunity_score": round(opportunity_score, 1),
        "months_of_inventory": round(months_of_inventory, 2),
        "momentum_state": momentum_state,
        "recommended_corridor": target_pricing_strategy
    }

# ---------------------------------------------------------
# VERIFICATION & RUNNING STEP 2 WITH SAMPLE MARKET DATA
# ---------------------------------------------------------

# Example Market Counts for a target "Buyer Zone"
sold_90 = 24
pending = 8
active_listings = 12
failed_listings = 4

dynamics = calculate_market_dynamics_engine(
    sold_90_days=sold_90,
    under_contract=pending,
    active=active_listings,
    expired_withdrawn=failed_listings,
    seasonality="Peak"
)

print("--- STEP 2 ENGINE OUTPUT ---")
print(f"Desirability (Odds of Selling): {dynamics['odds_of_selling_pct']}%")
print(f"Opportunity Score (Demand Gap): {dynamics['opportunity_score']} buyers")
print(f"Months of Inventory (MOI):     {dynamics['months_of_inventory']} months")
print(f"Market Momentum:               {dynamics['momentum_state']}")
print(f"Strategy Guidance:             {dynamics['recommended_corridor']}")