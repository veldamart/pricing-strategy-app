import pandas as pd
import numpy as np

def calculate_bridge_pricing_engine(base_price, momentum_state, increment=25000):
    """
    Step 4: MLS Bridge Pricing & Strategy Engine
    
    Parameters:
    - base_price: Float, baseline calculated price from Step 1
    - momentum_state: Str, 'Seller Advantage', 'Balanced Market', or 'Buyer Advantage'
    - increment: Int, typical search threshold steps ($25,000 or $50,000)
    
    Returns:
    - Dict with exact threshold bridges, strategic listing price, and search rationale
    """
    
    # 1. Calculate Nearest MLS Search Bridges (Lower & Upper Bounds)
    lower_bridge = (base_price // increment) * increment
    upper_bridge = lower_bridge + increment
    midpoint_bridge = lower_bridge + (increment / 2)
    
    # 2. Strategy Selection Based on Market Momentum (Step 2 Output)
    if momentum_state == "Seller Advantage":
        # Push toward or slightly above upper search threshold
        recommended_price = upper_bridge
        strategy_type = "Upper Threshold Capture (Stretch Strategy)"
        search_visibility = f"Captures buyers searching UP TO ${upper_bridge:,.0f} and starting AT ${upper_bridge:,.0f}."
        
    elif momentum_state == "Buyer Advantage":
        # Anchor at or below lower search threshold
        recommended_price = lower_bridge
        strategy_type = "Lower Threshold Anchor (Value Strategy)"
        search_visibility = f"Captures buyers searching UP TO ${lower_bridge:,.0f} to trigger fast market absorption."
        
    else:  # Balanced Market
        # Position at key bridge boundary or midpoint depending on proximity
        if abs(base_price - lower_bridge) < abs(base_price - upper_bridge):
            recommended_price = lower_bridge
        else:
            recommended_price = upper_bridge
            
        strategy_type = "Balanced Bridge Boundary"
        search_visibility = f"Positions property on major search boundary (${recommended_price:,.0f}) for maximum exposure."

    # 3. Micro-Psychological Adjustment Option (e.g., $749,900 vs $750,000)
    psychological_price = recommended_price - 100

    return {
        "raw_base_price": base_price,
        "lower_search_bridge": lower_bridge,
        "upper_search_bridge": upper_bridge,
        "recommended_list_price": recommended_price,
        "psychological_option": psychological_price,
        "strategy_type": strategy_type,
        "search_visibility_impact": search_visibility
    }

# ---------------------------------------------------------
# VERIFICATION & RUNNING STEP 4 WITH PIPELINED INPUTS
# ---------------------------------------------------------

# Inputs carried over from previous modules
base_price_input = 537450.00  # Calculated from Step 1
momentum_input = "Seller Advantage"  # Determined in Step 2

bridge_results = calculate_bridge_pricing_engine(
    base_price=base_price_input, 
    momentum_state=momentum_input, 
    increment=25000
)

print("--- STEP 4 ENGINE OUTPUT ---")
print(f"Calculated Raw Valuation:  ${bridge_results['raw_base_price']:,.2f}")
print(f"Nearest MLS Thresholds:    ${bridge_results['lower_search_bridge']:,.0f}  <--->  ${bridge_results['upper_search_bridge']:,.0f}")
print(f"\nRecommended List Price:   ${bridge_results['recommended_list_price']:,.0f}")
print(f"Psychological Variant:     ${bridge_results['psychological_option']:,.0f}")
print(f"Strategy Assigned:         {bridge_results['strategy_type']}")
print(f"MLS Search Impact:         {bridge_results['search_visibility_impact']}")