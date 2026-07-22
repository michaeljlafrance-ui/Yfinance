if len(df) > 0:
        # 1. Calculate percentage performance relative to 9:30 AM Open
        spy_base = df['Open_SPY'].iloc[0]
        dia_base = df['Open_DIA'].iloc[0]
        
        df['SPY_Pct'] = ((df['Close_SPY'] - spy_base) / spy_base) * 100
        df['DIA_Pct'] = ((df['Close_DIA'] - dia_base) / dia_base) * 100
        df['Spread'] = df['SPY_Pct'] - df['DIA_Pct']
        
        # 2. Extract latest values explicitly FIRST
        latest = df.iloc[-1]
        latest_spy = latest['SPY_Pct']
        latest_dia = latest['DIA_Pct']
        latest_spread = latest['Spread']
        
        # 3. Display Key Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("SPY (S&P 500) % Change", f"{latest_spy:+.3f}%")
        col2.metric("DIA (Dow Jones) % Change", f"{latest_dia:+.3f}%")
        col3.metric("Current Spread Gap", f"{latest_spread:+.3f}%")
        
        # 4. Strategy Signal Logic & Limit Target Math
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
