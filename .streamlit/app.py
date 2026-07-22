import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Streamlit Page Config
st.set_page_config(
    page_title="Intermarket Divergence Scanner",
    page_icon="📈",
    layout="wide"
)

# Load API credentials from secrets or fallback
API_KEY = st.secrets.get("RAPIDAPI_KEY", "932206dd22mshf288a41328bab03p12d137jsn9b24ebdfb34c")
HOST = "yahoo-finance166.p.rapidapi.com"

# App Title & Layout Header
st.title("⚡ 9:30 AM Divergence & Momentum Tracker")
st.caption("Tracks real-time 1-minute correlation and relative strength between S&P 500 (SPY) and Dow Jones (DIA)")

# Sidebar Controls
st.sidebar.header("Strategy Settings")
spread_threshold = st.sidebar.slider("Divergence Threshold (%)", min_value=0.02, max_value=0.50, value=0.10, step=0.01)
auto_refresh = st.sidebar.checkbox("Auto Refresh Page", value=False)

if auto_refresh:
    st.sidebar.caption("Refreshing every 60 seconds...")

# Data Fetching Function with Safety Checks
@st.cache_data(ttl=30)
def fetch_1min_candles(symbol):
    url = f"https://{HOST}/api/stock/get-chart"
    querystring = {
        "symbol": symbol,
        "interval": "1m",
        "range": "1d",
        "region": "US"
    }
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": HOST
    }

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # Defensive check for API payload
            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                
                if 'timestamp' in result and 'indicators' in result:
                    timestamps = result['timestamp']
                    quote = result['indicators']['quote'][0]
                    
                    df = pd.DataFrame({
                        'Timestamp': pd.to_datetime(timestamps, unit='s'),
                        'Close': quote.get('close', []),
                        'Open': quote.get('open', [])
                    }).dropna()
                    
                    # Convert timestamp to US Eastern Time
                    if not df.empty:
                        df['Timestamp'] = df['Timestamp'].dt.tz_localize('UTC').dt.tz_convert('America/New_York')
                    return df
                    
        st.error(f"API returned no chart data for {symbol}.")
        return None
    except Exception as e:
        st.error(f"Failed to fetch data for {symbol}: {e}")
        return None

# Load Data
with st.spinner("Fetching live 1-minute market feeds..."):
    spy_df = fetch_1min_candles("SPY")
    dia_df = fetch_1min_candles("DIA")

# Verify both DataFrames exist and are not empty BEFORE continuing
if spy_df is not None and dia_df is not None and not spy_df.empty and not dia_df.empty:
    
    # Merge datasets on timestamp
    df = pd.merge(spy_df, dia_df, on='Timestamp', suffixes=('_SPY', '_DIA'))
    
    # Filter for today's market open (9:30 AM EST onwards)
    df = df[df['Timestamp'].dt.time >= datetime.strptime("09:30", "%H:%M").time()].copy()
    
    if len(df) > 0:
        # Calculate percentage performance relative to 9:30 AM Open
        spy_base = df['Open_SPY'].iloc[0]
        dia_base = df['Open_DIA'].iloc[0]
        
        df['SPY_Pct'] = ((df['Close_SPY'] - spy_base) / spy_base) * 100
        df['DIA_Pct'] = ((df['Close_DIA'] - dia_base) / dia_base) * 100
        df['Spread'] = df['SPY_Pct'] - df['DIA_Pct']
        
        # Latest values
        latest = df.iloc[-1]
        latest_spy = latest['SPY_Pct']
        latest_dia = latest['DIA_Pct']
        latest_spread = latest['Spread']
        
        # Display Key Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("SPY (S&P 500) % Change", f"{latest_spy:+.3f}%")
        col2.metric("DIA (Dow Jones) % Change", f"{latest_dia:+.3f}%")
        col3.metric("Current Spread Gap", f"{latest_spread:+.3f}%")
        
        # Strategy Signal Logic & Limit Targets
        st.subheader("Signal Status")
        if latest_spy > 0 and latest_dia > 0:
            if latest_spread >= spread_threshold:
                # DIA is lagging SPY
                current_dia_price = latest['Close_DIA']
                target_sell_price = dia_base * (1 + (latest_spy / 100))
                
                st.success(f"""
                ### 🟢 BUY SIGNAL: DIA (Dow Jones)
                * **Action:** BUY DIA
                * **Current Price:** ${current_dia_price:.2f}
                * **Limit Sell Target:** **${target_sell_price:.2f}** (Targeting +{latest_spy - latest_dia:.2f}% catch-up)
                * **Reason:** SPY leads (+{latest_spy:.2f}%), DIA lags (+{latest_dia:.2f}%).
                """)
                
            elif latest_spread <= -spread_threshold:
                # SPY is lagging DIA
                current_spy_price = latest['Close_SPY']
                target_sell_price = spy_base * (1 + (latest_dia / 100))
                
                st.success(f"""
                ### 🟢 BUY SIGNAL: SPY (S&P 500)
                * **Action:** BUY SPY
                * **Current Price:** ${current_spy_price:.2f}
                * **Limit Sell Target:** **${target_sell_price:.2f}** (Targeting +{latest_dia - latest_spy:.2f}% catch-up)
                * **Reason:** DIA leads (+{latest_dia:.2f}%), SPY lags (+{latest_spy:.2f}%).
                """)
            else:
                st.info("⚖️ **BALANCED / NO DIVERGENCE**: Both indices are moving in tight correlation.")
        elif latest_spy < 0 and latest_dia < 0:
            st.warning("🔻 **BOTH DOWN**: Market is declining from open. Long signals paused.")
        else:
            st.info("👀 **MIXED DIRECTION**: Indices splitting direction. Waiting for synchronized breakout.")

        # Plotting Interactive Chart
        st.subheader("1-Minute Performance Overlay")
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['Timestamp'], y=df['SPY_Pct'],
            mode='lines', name='SPY (S&P 500)',
            line=dict(color='#00F0FF', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=df['Timestamp'], y=df['DIA_Pct'],
            mode='lines', name='DIA (Dow Jones)',
            line=dict(color='#FF007F', width=2)
        ))
        
        fig.update_layout(
            template='plotly_dark',
            xaxis_title="Time (EST)",
            yaxis_title="% Change from 9:30 AM Open",
            hovermode="x unified",
            margin=dict(l=20, r=20, t=30, b=20),
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # Raw data table
        with st.expander("View 1-Minute Tick Log"):
            st.dataframe(df[['Timestamp', 'Close_SPY', 'SPY_Pct', 'Close_DIA', 'DIA_Pct', 'Spread']].sort_values(by='Timestamp', ascending=False))
            
    else:
        st.warning("No data found for today's session starting at 9:30 AM EST. If market is closed, data will appear on market open.")
else:
    st.info("Awaiting valid price feeds from RapidAPI... Check your API key or try refreshing.")
