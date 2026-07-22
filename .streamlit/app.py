# Strategy Signal Logic & Limit Target Math
if latest_spy > 0 and latest_dia > 0:
    if latest_spread >= spread_threshold:
        # DIA is lagging SPY
        current_dia_price = latest['Close_DIA']
        # Calculate Target Limit Sell Price (Catch up to SPY % gain)
        target_sell_price = dia_base * (1 + (latest_spy / 100))
        
        st.success(f"""
        ### 🟢 BUY SIGNAL: DIA (Dow Jones)
        * **Action:** BUY DIA
        * **Current Price:** ${current_dia_price:.2f}
        * **Limit Sell Target:** **${target_sell_price:.2f}** (Expected +{latest_spy - latest_dia:.2f}% catch-up)
        * **Reason:** SPY is up +{latest_spy:.2f}%, DIA lags at +{latest_dia:.2f}%.
        """)
        
    elif latest_spread <= -spread_threshold:
        # SPY is lagging DIA
        current_spy_price = latest['Close_SPY']
        target_sell_price = spy_base * (1 + (latest_dia / 100))
        
        st.success(f"""
        ### 🟢 BUY SIGNAL: SPY (S&P 500)
        * **Action:** BUY SPY
        * **Current Price:** ${current_spy_price:.2f}
        * **Limit Sell Target:** **${target_sell_price:.2f}** (Expected +{latest_dia - latest_spy:.2f}% catch-up)
        * **Reason:** DIA is up +{latest_dia:.2f}%, SPY lags at +{latest_spy:.2f}%.
        """)
