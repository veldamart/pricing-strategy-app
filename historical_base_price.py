import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

def calculate_base_price_engine(df_sold, subject_sqft, iqr_threshold=1.5):
    """
    Step 1: Historical Base Price Engine
    
    Parameters:
    - df_sold: DataFrame containing 'Finished_SqFt' and 'Sold_Price'
    - subject_sqft: Integer/Float, finished square footage of subject property
    - iqr_threshold: Multiplier for IQR outlier removal (default 1.5)
    
    Returns:
    - Dict with regression metrics, clean dataset, and calculated base price
    """
    df = df_sold.copy()
    
    # 1. Outlier Removal via Interquartile Range (IQR) on Price per SqFt
    df['Price_Per_SqFt'] = df['Sold_Price'] / df['Finished_SqFt']
    q1 = df['Price_Per_SqFt'].quantile(0.25)
    q3 = df['Price_Per_SqFt'].quantile(0.75)
    iqr = q3 - q1
    
    lower_bound = q1 - (iqr_threshold * iqr)
    upper_bound = q3 + (iqr_threshold * iqr)
    
    # Filter non-outlier rows
    clean_df = df[(df['Price_Per_SqFt'] >= lower_bound) & (df['Price_Per_SqFt'] <= upper_bound)].copy()
    outliers = df[(df['Price_Per_SqFt'] < lower_bound) | (df['Price_Per_SqFt'] > upper_bound)]
    
    # 2. Linear Regression (y = mx + b)
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        clean_df['Finished_SqFt'], 
        clean_df['Sold_Price']
    )
    
    # 3. Base Price Calculation & Baseline Range (+/- 5%, rounded to nearest $10,000)
    base_price = (slope * subject_sqft) + intercept
    low_range = round((base_price * 0.95) / 10000) * 10000
    high_range = round((base_price * 1.05) / 10000) * 10000
    
    return {
        "slope_sqft_val": slope,
        "intercept_lot_val": intercept,
        "r_squared": r_value**2,
        "base_price": base_price,
        "baseline_range": (low_range, high_range),
        "clean_df": clean_df,
        "outliers": outliers
    }

# ---------------------------------------------------------
# VERIFICATION & RUNNING STEP 1 WITH MOCK DATA
# ---------------------------------------------------------

mock_sales = pd.DataFrame({
    'Address': ['101 Main St', '104 Main St', '108 Main St', '112 Main St', '115 Main St', '120 Main St', '999 Outlier Rd'],
    'Finished_SqFt': [1800, 2100, 2300, 2600, 2900, 3200, 2500],
    'Sold_Price': [420000, 475000, 510000, 565000, 615000, 680000, 200000] # Last item is a teardown outlier
})

subject_sqft_input = 2450
results = calculate_base_price_engine(mock_sales, subject_sqft_input)

print(f"--- STEP 1 ENGINE OUTPUT ---")
print(f"Lot Baseline Value (Intercept): ${results['intercept_lot_val']:,.2f}")
print(f"Building Value Slope:           ${results['slope_sqft_val']:,.2f} / sqft")
print(f"R-Squared (Model Fit):          {results['r_squared']:.4f}")
print(f"Outliers Dropped:               {len(results['outliers'])} row(s)")
print(f"\nCalculated Base Price:         ${results['base_price']:,.2f}")
print(f"Baseline Range (+/- 5%):        ${results['baseline_range'][0]:,.0f} - ${results['baseline_range'][1]:,.0f}")