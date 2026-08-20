import io
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy import stats

# ReportLab Imports for PDF Generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

st.set_page_config(page_title="Competitive Positioning Pricing Calculator", layout="wide")

st.title("🏡 Real Estate Competitive Positioning Pricing Calculator")
st.markdown("Automated valuation engine combining historical regression, market dynamics, and competitive positioning.")

# --- SIDEBAR INPUTS ---
st.sidebar.header("1. Subject Property")

# Read query parameters passed from your PHP lead form
query_params = st.query_params

# Safely extract 'sqft' from URL, falling back to default 2450 if missing or invalid
try:
    default_sqft = int(query_params.get("sqft", 2450))
except (ValueError, TypeError):
    default_sqft = 2450

subject_sqft = st.sidebar.number_input(
    "Finished Square Feet", 
    min_value=500, 
    max_value=10000, 
    value=default_sqft, 
    step=50
)

st.sidebar.header("2. Market Dynamics (90 Days)")
sold_90_days = st.sidebar.number_input("Sold Properties (Last 90 Days)", min_value=1, value=24)
under_contract = st.sidebar.number_input("Under Contract Listings", min_value=0, value=8)
active_count = st.sidebar.number_input("Active Listings", min_value=1, value=12)
expired_count = st.sidebar.number_input("Expired / Withdrawn Listings", min_value=0, value=4)
seasonality = st.sidebar.selectbox("Seasonality Mode", ["Peak", "Transition", "Off-Season"])
bridge_increment = st.sidebar.selectbox("MLS Search Bridge Increment", [25000, 50000, 100000], index=0)

# --- DATA INGESTION ---
st.subheader("📂 Step 1 Data Ingestion: Upload & Fine-Tune MLS Data")

col_sold_upload, col_active_upload = st.columns(2)
with col_sold_upload:
    sold_file = st.file_uploader("Upload Historical Solds (CSV)", type=["csv"], key="sold_csv")
with col_active_upload:
    active_file = st.file_uploader("Upload Active Competition (CSV)", type=["csv"], key="active_csv")

def map_and_clean_df(uploaded_file, file_label):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        cols = list(df.columns)
        
        default_price = next((c for c in cols if 'price' in c.lower() or 'sold' in c.lower() or 'list' in c.lower()), cols[0])
        default_sqft = next((c for c in cols if 'sqft' in c.lower() or 'square' in c.lower() or 'area' in c.lower()), cols[0])
        default_addr = next((c for c in cols if 'address' in c.lower() or 'street' in c.lower() or 'prop' in c.lower()), cols[0])
        
        c1, c2, c3 = st.columns(3)
        price_col = c1.selectbox(f"Price Column ({file_label})", cols, index=cols.index(default_price), key=f"{file_label}_price")
        sqft_col = c2.selectbox(f"SqFt Column ({file_label})", cols, index=cols.index(default_sqft), key=f"{file_label}_sqft")
        addr_col = c3.selectbox(f"Address Column ({file_label})", cols, index=cols.index(default_addr), key=f"{file_label}_addr")
        
        clean_df = pd.DataFrame({
            'Address': df[addr_col].astype(str),
            'Finished_SqFt': pd.to_numeric(df[sqft_col].astype(str).str.replace(r'[\$,]', '', regex=True), errors='coerce'),
            'Price': pd.to_numeric(df[price_col].astype(str).str.replace(r'[\$,]', '', regex=True), errors='coerce')
        }).dropna()
        return clean_df
    return None

df_sold_raw = map_and_clean_df(sold_file, "Solds")
df_active_raw = map_and_clean_df(active_file, "Actives")

if df_sold_raw is None:
    df_sold_raw = pd.DataFrame({
        'Address': ['101 Main St', '104 Main St', '108 Main St', '112 Main St', '115 Main St', '120 Main St', '999 Teardown Rd'],
        'Finished_SqFt': [1800, 2100, 2300, 2600, 2900, 3200, 2500],
        'Price': [420000, 475000, 510000, 565000, 615000, 680000, 200000]
    })

if df_active_raw is None:
    df_active_raw = pd.DataFrame({
        'Address': ['201 Oak St', '205 Oak St', '210 Oak St', '215 Oak St', '220 Oak St'],
        'Finished_SqFt': [2200, 2600, 2100, 2800, 2300],
        'Price': [520000, 580000, 545000, 620000, 510000]
    })

# --- MANUAL OUTLIER SELECTION TABLE ---
st.markdown("### 🛠️ Historical Sales: Inclusion & Outlier Management")
df_sold_raw['Price_Per_SqFt'] = df_sold_raw['Price'] / df_sold_raw['Finished_SqFt']
q1, q3 = df_sold_raw['Price_Per_SqFt'].quantile([0.25, 0.75])
iqr = q3 - q1
lower_bound = q1 - (1.5 * iqr)
upper_bound = q3 + (1.5 * iqr)

df_sold_raw['Include_In_Model'] = (df_sold_raw['Price_Per_SqFt'] >= lower_bound) & (df_sold_raw['Price_Per_SqFt'] <= upper_bound)

edited_solds = st.data_editor(
    df_sold_raw[['Include_In_Model', 'Address', 'Finished_SqFt', 'Price', 'Price_Per_SqFt']],
    column_config={
        "Include_In_Model": st.column_config.CheckboxColumn("Include?"),
        "Price": st.column_config.NumberColumn("Sold Price", format="$%d"),
        "Price_Per_SqFt": st.column_config.NumberColumn("$/SqFt", format="$%.2f"),
        "Finished_SqFt": st.column_config.NumberColumn("SqFt", format="%d")
    },
    disabled=["Address", "Finished_SqFt", "Price", "Price_Per_SqFt"],
    hide_index=True,
    use_container_width=True
)

clean_solds = edited_solds[edited_solds['Include_In_Model'] == True].copy()

# --- ENGINE CALCULATIONS ---
if len(clean_solds) >= 2:
    slope, intercept, r_val, _, _ = stats.linregress(clean_solds['Finished_SqFt'], clean_solds['Price'])
    base_price = (slope * subject_sqft) + intercept
    r_squared = r_val ** 2
else:
    st.error("Please select at least 2 properties to calculate regression analysis.")
    st.stop()

total_attempted = sold_90_days + active_count + expired_count
odds_of_selling = (sold_90_days / total_attempted * 100) if total_attempted > 0 else 0.0
season_mults = {"Peak": 1.15, "Transition": 1.0, "Off-Season": 0.85}
proj_demand = sold_90_days * season_mults.get(seasonality, 1.0)
opportunity_score = proj_demand - under_contract

monthly_sales = sold_90_days / 3.0
moi = (active_count / monthly_sales) if monthly_sales > 0 else 999.0
momentum_state = "Seller Advantage" if moi < 3.0 else ("Balanced Market" if moi <= 5.0 else "Buyer Advantage")

lower_bridge = (base_price // bridge_increment) * bridge_increment
upper_bridge = lower_bridge + bridge_increment
rec_price = upper_bridge if momentum_state == "Seller Advantage" else (lower_bridge if momentum_state == "Buyer Advantage" else lower_bridge)

df_a = df_active_raw.copy()
subject_row = pd.DataFrame([{'Address': '*** SUBJECT PROPERTY ***', 'Finished_SqFt': subject_sqft, 'Price': rec_price}])
comp_df = pd.concat([df_a, subject_row], ignore_index=True)
med_price = comp_df['Price'].median()
med_sqft = comp_df['Finished_SqFt'].median()

# --- PDF GENERATOR FUNCTION ---
def generate_pdf_report(rec_price, base_price, odds_of_selling, momentum_state, subject_sqft, moi, r_squared):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=20, leading=24, textColor=colors.HexColor('#1E3A8A'))
    h2_style = ParagraphStyle('H2Style', parent=styles['Heading2'], fontSize=14, leading=18, textColor=colors.HexColor('#1E3A8A'))
    normal_style = styles['Normal']
    
    # Document Header
    story.append(Paragraph("<b>COMPETITIVE POSITIONING PRICING REPORT</b>", title_style))
    story.append(Paragraph("Prepared for Listing Presentation", normal_style))
    story.append(Spacer(1, 15))
    
    # Key Summary Metrics Table
    data = [
        ["Metric", "Value"],
        ["Recommended List Price", f"${rec_price:,.0f}"],
        ["Base Model Valuation", f"${base_price:,.0f}"],
        ["Subject Square Footage", f"{subject_sqft:,} sqft"],
        ["Market Momentum", momentum_state],
        ["Months of Inventory (MOI)", f"{moi:.1f} Months"],
        ["Odds of Selling (90-Day)", f"{odds_of_selling:.1f}%"],
        ["Regression Accuracy (R²)", f"{r_squared:.3f}"]
    ]
    
    t = Table(data, colWidths=[250, 250])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0,0), (1,0), colors.white),
        ('FONTNAME', (0,0), (1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F8FAFC')),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))
    
    # Strategic Guidance
    story.append(Paragraph("<b>Strategic Pricing Guidance</b>", h2_style))
    story.append(Spacer(1, 5))
    
    strategy_text = f"""
    Based on recent 90-day market movement, the local market exhibits a <b>{momentum_state}</b> environment with 
    <b>{moi:.1f} months of inventory</b>. The target list price of <b>${rec_price:,.0f}</b> is strategic: it anchors the property 
    directly on a major MLS search threshold boundary, capturing overlapping digital buyer searches while aligning directly 
    with current supply and demand absorption rates.
    """
    story.append(Paragraph(strategy_text, normal_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- DASHBOARD LAYOUT & PDF DOWNLOAD ---
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Recommended List Price", f"${rec_price:,.0f}")
col2.metric("Base Valuation", f"${base_price:,.0f}")
col3.metric("Odds of Selling", f"{odds_of_selling:.1f}%")
col4.metric("Market Momentum", momentum_state)

st.markdown("---")

# PDF Download Section
pdf_bytes = generate_pdf_report(rec_price, base_price, odds_of_selling, momentum_state, subject_sqft, moi, r_squared)
st.download_button(
    label="📄 Download Client-Ready PDF Report",
    data=pdf_bytes,
    file_name=f"Pricing_Report_{subject_sqft}sqft.pdf",
    mime="application/pdf"
)

st.markdown("---")

tab1, tab2 = st.tabs(["📊 Historical Trendline (Step 1)", "🎯 Competitive Matrix (Step 3)"])

with tab1:
    st.subheader("Historical Sales Trendline Regression")
    fig1 = px.scatter(
        edited_solds, 
        x='Finished_SqFt', 
        y='Price', 
        color='Include_In_Model',
        color_discrete_map={True: "#1f77b4", False: "#d62728"},
        hover_data=['Address'], 
        title="Finished SqFt vs. Sold Price"
    )
    fig1.add_scatter(x=clean_solds['Finished_SqFt'], y=(slope * clean_solds['Finished_SqFt'] + intercept), mode='lines', name='Regression Line', line=dict(color='gray', dash='dash'))
    fig1.add_scatter(x=[subject_sqft], y=[base_price], mode='markers', marker=dict(size=16, color='gold', symbol='star'), name='Subject Base Price')
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    st.subheader("Active Listing Positioning Matrix")
    fig2 = px.scatter(comp_df, x='Finished_SqFt', y='Price', hover_data=['Address'], color='Address', title="Active Competition")
    fig2.add_hline(y=med_price, line_dash="dash", annotation_text="Median Price")
    fig2.add_vline(x=med_sqft, line_dash="dash", annotation_text="Median Size")
    st.plotly_chart(fig2, use_container_width=True)

st.success(f"**Strategy Note:** Market is currently in a **{momentum_state}** ({moi:.1f} Months of Inventory). Target listing price is anchored to the MLS Bridge at **${rec_price:,.0f}**.")