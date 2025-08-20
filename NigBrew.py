import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# === Load Data ===
@st.cache_data
def load_data(path="nb_analytics_small.xlsx"):
    xls = pd.ExcelFile(path, engine="openpyxl")
    dfs = {}
    for sheet in xls.sheet_names:
        dfs[sheet] = pd.read_excel(xls, sheet)
    return dfs

dfs = load_data()

# --- Utility ---
def safe_revenue(df):
    if "revenue" in df.columns:
        return df
    elif "qty" in df.columns and "effective_price" in df.columns:
        df["revenue"] = df["qty"] * df["effective_price"]
    elif "qty" in df.columns and "list_price" in df.columns:
        df["revenue"] = df["qty"] * df["list_price"]
    else:
        df["revenue"] = 0
    return df

# Apply filters
def apply_filters(df):
    if "state" in df.columns and state_filter:
        df = df[df["state"].isin(state_filter)]
    if "sku" in df.columns and sku_filter:
        df = df[df["sku"].isin(sku_filter)]
    return df

# === Sidebar Filters ===
st.sidebar.header("Filters")
state_filter = st.sidebar.multiselect("Select States", dfs["nb_fact_sales"].get("state", []).unique())
sku_filter = st.sidebar.multiselect("Select SKUs", dfs["nb_fact_sales"].get("sku", []).unique())

# Reset button
if st.sidebar.button("Reset Filters"):
    state_filter = []
    sku_filter = []

# Page Configuration
st.set_page_config(page_title="Nigerian Breweries Analytics Dashboard", layout="wide", page_icon="🍺")
# === Executive Summary ===
st.title("📊 Nigerian Breweries Executive Dashboard")

sales_df = safe_revenue(dfs["nb_fact_sales"])
filtered_sales = apply_filters(sales_df)

rev_total = filtered_sales["revenue"].sum()
units_total = filtered_sales.get("qty", pd.Series([0])).sum()
oos_rate = filtered_sales.get("oos_rate", pd.Series([0])).mean()

col1, col2, col3 = st.columns(3)
col1.metric("Total Revenue", f"₦{rev_total/1e9:.1f}B")
col2.metric("Units Sold", f"{units_total/1e6:.1f}M")
col3.metric("Avg OOS Rate", f"{oos_rate:.1%}")

st.markdown("---")

st.subheader("Executive Highlights")
# Top states
state_rev = filtered_sales.groupby("state", as_index=False).agg(revenue=("revenue","sum"))
if not state_rev.empty:
    top_state = state_rev.sort_values("revenue", ascending=False).head(1)
    highlight1 = f"**{top_state.iloc[0]['state']}** drives highest revenue at ₦{top_state.iloc[0]['revenue']/1e9:.1f}B."
else:
    highlight1 = "No states match current filter."

# Distributor risk
if "nb_distributor_kpis" in dfs:
    dist = dfs["nb_distributor_kpis"].copy()
    dist = apply_filters(dist)
    dist["risk_score"] = (0.25*(dist["credit_utilization"]>0.85)
                          +0.25*(dist["dso_days"]>45)
                          -0.2*(dist["otif_ratio"]>0.9)
                          + dist.get("churn_risk",0)).clip(0,1)
    if not dist.empty:
        risky = dist.sort_values("risk_score", ascending=False).head(1)
        highlight2 = f"Distributor **{risky.iloc[0]['distributor']}** shows elevated risk (score {risky.iloc[0]['risk_score']:.2f})."
    else:
        highlight2 = "No distributor data under current filter."
else:
    highlight2 = "Distributor risk data not available."

# Pricing gap
if "nb_pricing_promotions" in dfs:
    price_df = apply_filters(dfs["nb_pricing_promotions"])
    if not price_df.empty:
        avg_gap = price_df.get("price_gap_vs_comp", pd.Series([0])).mean()
        highlight3 = f"Average price gap vs competitors is {avg_gap:.2f} (₦)."
    else:
        highlight3 = "No pricing data under current filter."
else:
    highlight3 = "Pricing data not available."

st.write("- ", highlight1)
st.write("- ", highlight2)
st.write("- ", highlight3)

st.markdown("---")

# === Tabs for Deep Dive ===
tabs = st.tabs(["Sales", "Logistics", "Distributor Risk", "Social & Media", "Macro Simulator", "Heatmaps & Cross Tabs", "Data Dictionary"])

with tabs[0]:
    st.subheader("Sales Trend")
    if "date" in filtered_sales.columns:
        filtered_sales["date"] = pd.to_datetime(filtered_sales["date"], errors="coerce")
        trend = filtered_sales.groupby(pd.Grouper(key="date", freq="M")).agg(revenue=("revenue","sum")).reset_index()
        fig = px.line(trend, x="date", y="revenue", title="Monthly Revenue Trend")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top States by Revenue")
    if not state_rev.empty:
        fig2 = px.bar(state_rev.sort_values("revenue", ascending=False).head(5), x="state", y="revenue")
        st.plotly_chart(fig2, use_container_width=True)

with tabs[1]:
    st.subheader("Logistics – Cost per KM")
    if "nb_logistics" in dfs:
        log_df = dfs["nb_logistics"].copy()
        log_df = apply_filters(log_df)
        log_df["cost_per_km"] = log_df["freight_cost_ngn"] / log_df["distance_km"].replace(0, pd.NA)
        if not log_df.empty:
            fig3 = px.bar(log_df.groupby("state").cost_per_km.mean().reset_index(), x="state", y="cost_per_km", title="Avg Cost per KM by State")
            st.plotly_chart(fig3, use_container_width=True)

with tabs[2]:
    st.subheader("Distributor Risk Radar")
    if "nb_distributor_kpis" in dfs:
        top5 = dist.sort_values("risk_score", ascending=False).head(5)
        if not top5.empty:
            categories = ["credit_utilization", "dso_days", "otif_ratio", "churn_risk"]
            fig4 = go.Figure()
            for _, row in top5.iterrows():
                fig4.add_trace(go.Scatterpolar(r=[row[categories].fillna(0).max() for c in categories],
                                               theta=categories,
                                               fill='toself', name=row['distributor']))
            fig4.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True)
            st.plotly_chart(fig4, use_container_width=True)

with tabs[3]:
    st.subheader("Social Media Sentiment & Share of Voice")
    if "nb_social_listening" in dfs:
        soc = apply_filters(dfs["nb_social_listening"])
        if "sentiment_pos" in soc.columns and "sentiment_neg" in soc.columns:
            soc["net_sentiment"] = soc["sentiment_pos"] - soc["sentiment_neg"]
            fig5 = px.bar(soc.groupby("brand").net_sentiment.mean().reset_index(), x="brand", y="net_sentiment")
            st.plotly_chart(fig5, use_container_width=True)
        if "mentions" in soc.columns:
            fig6 = px.bar(soc.groupby("platform").mentions.sum().reset_index(), x="platform", y="mentions")
            st.plotly_chart(fig6, use_container_width=True)

with tabs[4]:
    st.subheader("Macro Simulator")
    if "nb_macro_weather" in dfs:
        macro = dfs["nb_macro_weather"]
        inflation = st.slider("Inflation (%)", 0, 30, 15)
        fx = st.slider("FX NGN/USD", 500, 1500, 1000)
        impact = rev_total * (1 - (inflation/100)*0.2) * (1000/fx)
        st.metric("Projected Revenue", f"₦{impact/1e9:.1f}B")

with tabs[5]:
    st.subheader("Heatmaps & Cross Tabulations")
    # Revenue by State vs SKU heatmap
    if "sku" in filtered_sales.columns and "state" in filtered_sales.columns:
        pivot = filtered_sales.pivot_table(values="revenue", index="state", columns="sku", aggfunc="sum", fill_value=0)
        if not pivot.empty:
            fig7 = px.imshow(pivot, aspect="auto", color_continuous_scale="Blues", title="Revenue Heatmap: State vs SKU")
            st.plotly_chart(fig7, use_container_width=True)

    # Crosstab: Month vs State
    if "date" in filtered_sales.columns:
        filtered_sales["month"] = filtered_sales["date"].dt.to_period("M")
        cross = pd.crosstab(filtered_sales["month"], filtered_sales["state"], values=filtered_sales["revenue"], aggfunc="sum").fillna(0)
        if not cross.empty:
            fig8 = px.imshow(cross.T, aspect="auto", color_continuous_scale="Viridis", title="Revenue Crosstab: Month vs State")
            st.plotly_chart(fig8, use_container_width=True)

with tabs[6]:
    st.subheader("Data Dictionary")
    st.write("This app uses multiple sheets from nb_analytics_small.xlsx including sales, logistics, distributor KPIs, pricing, social, macro, etc.")

# Footer
st.markdown("---")
st.markdown("# About the Developer")

st.image("My image.jpg", width=250)
st.markdown("## **Kajola Gbenga**")

st.markdown(
    """
\U0001F4C7 Certified Data Analyst | Certified Data Scientist | Certified SQL Programmer | Mobile App Developer | AI/ML Engineer

\U0001F517 [LinkedIn](https://www.linkedin.com/in/kajolagbenga)  
\U0001F4DC [View My Certifications & Licences](https://www.datacamp.com/portfolio/kgbenga234)  
\U0001F4BB [GitHub](https://github.com/prodigy234)  
\U0001F310 [Portfolio](https://kajolagbenga.netlify.app/)  
\U0001F4E7 k.gbenga234@gmail.com
"""
)

st.markdown("✅ Created using Python and Streamlit")