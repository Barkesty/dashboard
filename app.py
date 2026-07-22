import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Outage Dispatch Dashboard", layout="wide")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('dashboard_data.csv')
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    return df

df = load_data()

# Sidebar configuration
st.sidebar.title("Dispatch Controls")

# District selector
district_list = sorted(df['district_name'].unique())
selected_district = st.sidebar.selectbox("Select District:", district_list)

# Date selector
min_date = df['Date'].min()
max_date = df['Date'].max()
selected_date = st.sidebar.slider("Select Forecast Date:", min_value=min_date, max_value=max_date, value=min_date)

# Filter data based on selection
district_df = df[df['district_name'] == selected_district].sort_values('Date')
daily_data = district_df[district_df['Date'] == selected_date]

if daily_data.empty:
    st.error("No data available for this date.")
else:
    row = daily_data.iloc[0]
    
    # Main dashboard layout
    st.title("Outage Dispatch Dashboard")
    st.markdown(f"**District:** {selected_district} | **Forecast Date:** {selected_date}")
    
    st.markdown("---")
    
    # ROW 1: Weather context with 5 selected features
    st.subheader("Environmental Context")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    col1.metric("Mean Air Temp", f"{row['2t_mean']:.1f} °C")
    col2.metric("Max Dew Point", f"{row['2d_max']:.1f} °C")
    col3.metric("Rainfall Sum", f"{row['tp_sum']:.1f} mm")
    col4.metric("Mean Snow Temp", f"{row['tsn_mean']:.4f} °C")
    col5.metric("Mean Soil Moisture", f"{row['swvl1_mean']:.4f}")
    
    st.markdown("---")
    
    # ROW 2: Dispatch recommendations
    st.subheader("Dispatch Recommendations and Risk Assessment")
    col6, col7, col8, col9, col10 = st.columns(5)
    
    col6.metric("Baseline (Most Likely)", f"{int(row['Display_Count_median'])} Faults")
    col7.metric("70% Worst-Case", f"{int(row['Display_Count_q_850'])} Faults")
    col8.metric("80% Worst-Case", f"{int(row['Display_Count_q_900'])} Faults")
    col9.metric("90% Worst-Case", f"{int(row['Display_Count_q_950'])} Faults")
    
    actual = int(row['Incident_Count'])
    delta = actual - int(row['Display_Count_median'])
    col10.metric("Actual Incidents", f"{actual}", delta=delta, delta_color="inverse")
   
    st.markdown("---")
    
    # Interactive line chart
    st.subheader("90-Day Probabilistic Trend")
    
    # Extract a 90-day window around the selected date
    window_df = district_df[(district_df['Date'] >= selected_date - pd.Timedelta(days=45)) & 
                            (district_df['Date'] <= selected_date + pd.Timedelta(days=45))]
    
    fig = go.Figure()
    
    # 90% Prediction Interval
    fig.add_trace(go.Scatter(x=window_df['Date'], y=window_df['Pred_Count_q_950'], mode='lines', line=dict(width=0), showlegend=False))
    fig.add_trace(go.Scatter(x=window_df['Date'], y=window_df['Pred_Count_q_050'], mode='lines', line=dict(width=0), 
                             fill='tonexty', fillcolor='rgba(255, 182, 193, 0.4)', name='90% Interval'))
    
    # 80% Prediction Interval
    fig.add_trace(go.Scatter(x=window_df['Date'], y=window_df['Pred_Count_q_900'], mode='lines', line=dict(width=0), showlegend=False))
    fig.add_trace(go.Scatter(x=window_df['Date'], y=window_df['Pred_Count_q_100'], mode='lines', line=dict(width=0), 
                             fill='tonexty', fillcolor='rgba(135, 206, 250, 0.5)', name='80% Interval'))
    
    # 70% Prediction Interval
    fig.add_trace(go.Scatter(x=window_df['Date'], y=window_df['Pred_Count_q_850'], mode='lines', line=dict(width=0), showlegend=False))
    fig.add_trace(go.Scatter(x=window_df['Date'], y=window_df['Pred_Count_q_150'], mode='lines', line=dict(width=0), 
                             fill='tonexty', fillcolor='rgba(144, 238, 144, 0.5)', name='70% Interval'))
    
    # Median Prediction
    fig.add_trace(go.Scatter(x=window_df['Date'], y=window_df['Pred_Count_median'], mode='lines', 
                             line=dict(color='#0055A4', width=3), name='Predicted Median'))
    
    # Actual Count
    fig.add_trace(go.Scatter(x=window_df['Date'], y=window_df['Incident_Count'], mode='markers+lines', 
                             marker=dict(color='#E65C00', size=6), line=dict(color='#E65C00', width=1, dash='dot'), name='Actual Faults'))
    
    # Draw a vertical line without annotation text to avoid Plotly calculation errors
    fig.add_vline(x=selected_date, line_width=2, line_dash="dash", line_color="gray")

    # Add text annotation separately
    fig.add_annotation(
        x=selected_date, 
        y=1.05, 
        yref="paper", 
        text="Selected Date", 
        showarrow=False, 
        font=dict(color="gray")
    )
    
    fig.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0), hovermode="x unified",
                      xaxis_title="Date", yaxis_title="Daily Incident Count")
    
    st.plotly_chart(fig, use_container_width=True)