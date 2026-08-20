import pandas as pd
import numpy as np

def calculate_positioning_matrix_engine(df_active, subject_sqft, subject_target_price):
    """
    Step 3: Competitive Positioning Matrix Engine
    
    Parameters:
    - df_active: DataFrame containing active listings with 'Address', 'Finished_SqFt', 'List_Price'
    - subject_sqft: Int/Float, size of subject property
    - subject_target_price: Float, target listing price for subject property
    
    Returns:
    - Dict with quadrant classification, relative ranks, and positioning metrics
    """
    df = df_active.copy()
    
    # 1. Add Subject Property to Active Dataframe for Relative Evaluation
    subject_row = pd.DataFrame([{
        'Address': '*** SUBJECT PROPERTY ***',
        'Finished_SqFt': subject_sqft,
        'List_Price': subject_target_price
    }])
    combined_df = pd.concat([df, subject_row], ignore_index=True)
    
    # 2. Establish Median Baselines for Price and Size
    median_price = combined_df['List_Price'].median()
    median_sqft = combined_df['Finished_SqFt'].median()
    
    # 3. Quadrant Classification Function
    def assign_quadrant(row):
        price = row['List_Price']
        sqft = row['Finished_SqFt']
        
        if price <= median_price and sqft >= median_sqft:
            return "Advantage (High Value/Size, Lower Price)"
        elif price > median_price and sqft >= median_sqft:
            return "Premium / High End (High Size, High Price)"
        elif price <= median_price and sqft < median_sqft:
            return "Entry Level / Compact (Low Size, Low Price)"
        else:
            return "Disadvantage (Overpriced / Low Size, High Price)"

    combined_df['Quadrant'] = combined_df.apply(assign_quadrant, axis=1)
    
    # 4. Extract Subject Property Position
    subject_info = combined_df[combined_df['Address'] == '*** SUBJECT PROPERTY ***'].iloc[0]
    
    # 5. Price & Size Rankings (1 = Best/Most Competitive)
    combined_df['Price_Rank'] = combined_df['List_Price'].rank(ascending=True) # Cheaper is higher rank
    combined_df['Size_Rank'] = combined_df['Finished_SqFt'].rank(ascending=False) # Larger is higher rank
    
    subject_price_rank = int(combined_df.loc[combined_df['Address'] == '*** SUBJECT PROPERTY ***', 'Price_Rank'].values[0])
    subject_size_rank = int(combined_df.loc[combined_df['Address'] == '*** SUBJECT PROPERTY ***', 'Size_Rank'].values[0])
    total_competitors = len(combined_df)

    return {
        "median_price": median_price,
        "median_sqft": median_sqft,
        "subject_quadrant": subject_info['Quadrant'],
        "price_rank": f"{subject_price_rank} of {total_competitors}",
        "size_rank": f"{subject_size_rank} of {total_competitors}",
        "matrix_df": combined_df
    }

# ---------------------------------------------------------
# VERIFICATION & RUNNING STEP 3 WITH MOCK ACTIVE DATA
# ---------------------------------------------------------

mock_active_listings = pd.DataFrame({
    'Address': ['201 Oak St', '205 Oak St', '210 Oak St', '215 Oak St', '220 Oak St'],
    'Finished_SqFt': [2200, 2600, 2100, 2800, 2300],
    'List_Price': [520000, 580000, 545000, 620000, 510000]
})

subject_sqft_input = 2450
subject_proposed_price = 535000 # Testing a candidate price from Step 1 & 2

matrix_results = calculate_positioning_matrix_engine(
    mock_active_listings, 
    subject_sqft_input, 
    subject_proposed_price
)

print("--- STEP 3 ENGINE OUTPUT ---")
print(f"Buyer Zone Median Price:  ${matrix_results['median_price']:,.2f}")
print(f"Buyer Zone Median Size:   {matrix_results['median_sqft']:.0f} sqft")
print(f"\nSubject Quadrant:         {matrix_results['subject_quadrant']}")
print(f"Price Competitiveness:    Ranked {matrix_results['price_rank']} (Lowest to Highest)")
print(f"Space Value Rank:         Ranked {subject_sqft_input} sqft ({matrix_results['size_rank']} Largest to Smallest)")