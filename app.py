import os
import streamlit as st

# גשר סודות: ב-Streamlit Cloud המפתחות מגיעים מ-st.secrets במקום מקובץ .env.
# מעבירים אותם למשתני סביבה כדי ש-data_engine/ai_core (שמשתמשים ב-os.getenv) יעבדו בשני המצבים.
try:
    for _k, _v in st.secrets.items():
        if isinstance(_v, str):
            os.environ.setdefault(_k, _v)
except Exception:
    pass

import pandas as pd
import plotly.graph_objects as go
from data_engine import fetch_us_data, calculate_technical_indicators, MonteCarloRiskEngine, run_live_data_background, send_phone_alert, get_quick_recommendation
from ai_core import analyze_stock_with_ai
from portfolio import load_portfolio, save_portfolio
from market_scanner import scan_market
from universe import get_universe

# הפעלת זרם הנתונים החי ברקע
if 'ws_running' not in st.session_state:
    run_live_data_background()
    st.session_state.ws_running = True

st.set_page_config(page_title="מנהל תיק השקעות AI", layout="wide", page_icon="📈")

# הגדרת עיצוב CSS לעברית (ימין לשמאל)
st.markdown("""
<style>
    body, .stApp { direction: rtl; text-align: right; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    h1, h2, h3, h4, h5, h6, p, div { text-align: right; }
    .stSelectbox label, .stTextInput label { text-align: right; display: block; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def get_processed_data(symbol):
    df = fetch_us_data(symbol, count=250)
    return calculate_technical_indicators(df)

st.title("🤖 מנהל תיק השקעות AI-Native")
st.markdown("מערכת ארגונית מונחית-אירועים (Event-Driven) עם מודל עלויות ריאלי, סריקת AI והתראות לטלפון.")

# ==========================================
# הפירמידה ההפוכה וכלל ה-5 שניות: מדדים חמים למעלה
# ==========================================
st.header("⚡ התראות ופעולות AI מיידיות")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.info("🟢 **AAPL: קנייה מיידית (BUY NOW)** \n\n *ביטחון:* 92% \n\n מומנטום חיובי בעקבות זרימת נתונים בזמן אמת.")
with col2:
    st.warning("🟠 **TEVA: החזק (HOLD)** \n\n *ביטחון:* 75% \n\n המתנה לפריצת התנגדות בשערי הסגירה.")
with col3:
    st.error("🔴 **TSLA: צמצם חשיפה (REDUCE)** \n\n *ביטחון:* 81% \n\n שבירת מגמה חריפה בסקטור החשמלי.")
with col4:
    if st.button("📲 שלח התראת מבחן לטלפון"):
        send_phone_alert("מערכת AI-Native: הכל תקין, המערכת מחוברת ומוכנה לפעולה!")
        st.success("התראה נשלחה!")

st.divider()

# ==========================================
# אזור המחקר וניהול הסיכונים 
# ==========================================
st.header("📊 חקר נכסים וסימולציית מונטה-קרלו")

c1, c2 = st.columns([9, 10])

with c1:
    st.subheader("בחר נכס לניתוח")
    symbol = st.text_input("סימול מניה (לדוגמה: AAPL)", value="AAPL")
    analyze_btn = st.button("🧠 הפעל ניתוח AI מקיף")

with c2:
    if symbol:
        df = get_processed_data(symbol)
        
        if not df.empty:
            returns = df['Close'].pct_change().dropna().values
            mc_engine = MonteCarloRiskEngine()
            risk_of_ruin, prob_prof, median_ret = mc_engine.run_simulation(returns, num_simulations=5000)
            
            rc1, rc2, rc3 = st.columns(3)
            rc1.metric("הסתברות למחיקת התיק (Risk of Ruin)", f"{risk_of_ruin*100:.2f}%", "קריטי" if risk_of_ruin > 0.05 else "בטוח", delta_color="inverse")
            rc2.metric("הסתברות לרווחיות בסימולציה", f"{prob_prof*100:.1f}%")
            rc3.metric("תוחלת תשואה חציונית", f"{median_ret*100:.2f}%")
            
            fig = go.Figure(data=[go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='מחיר')])
            fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA_20'], mode='lines', name='ממוצע נע 20', line=dict(color='#00ffcc')))
            fig.update_layout(title=f"גרף אינטראקטיבי - {symbol}", xaxis_title="תאריך", yaxis_title="מחיר (USD)", template="plotly_dark", margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)
            
            if analyze_btn:
                with st.spinner("ה-AI מנתח את הנתונים הטכניים והחדשות..."):
                    tech_snapshot = str(df[['Close', 'RSI_14', 'MACD']].tail(1).to_dict())
                    ai_result = analyze_stock_with_ai(symbol, tech_snapshot, "אין חדשות חריגות היום.")
                    st.success("**החלטת ה-AI (לוגיקה והסבר):**")
                    st.json(ai_result)
        else:
            st.warning("לא נמצאו נתונים. אנא בדוק את הסימול או את חיבור ה-API.")

st.divider()

# ==========================================
# תיק ההשקעות שלי - טבלה אינטראקטיבית + המלצות
# ==========================================
st.header("💼 תיק ההשקעות שלי")
st.markdown("ערוך את האחזקות שלך ישירות בטבלה — הוסף שורה בתחתית, או מחק שורה עם סימון ה-❌. לחץ **שמור** כדי לשמור.")

portfolio_df = load_portfolio()
edited_portfolio = st.data_editor(
    portfolio_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Symbol": st.column_config.TextColumn("סימול", help="סימול נסחר (לדוגמה AAPL), או מזהה כלשהו לקרן ישראלית."),
        "Name": st.column_config.TextColumn("שם נייר"),
        "Currency": st.column_config.SelectboxColumn("מטבע", options=["USD", "ILS"], default="USD"),
        "Quantity": st.column_config.NumberColumn("כמות", min_value=0),
        "BuyPrice": st.column_config.NumberColumn("מחיר קנייה ליחידה", format="%.2f"),
        "Benchmark": st.column_config.TextColumn("מדד עוקב", help="לקרן מחקה - הסימול של המדד שהיא עוקבת אחריו (לדוגמה ^TA125.TA, SOXX, MCHI). אם ריק - מנותח הסימול עצמו."),
    },
    key="portfolio_editor",
)

pc1, pc2 = st.columns([1, 4])
with pc1:
    if st.button("💾 שמור תיק"):
        save_portfolio(edited_portfolio)
        st.success("התיק נשמר!")
with pc2:
    analyze_portfolio_btn = st.button("🧠 נתח את כל התיק וקבל המלצות")

if analyze_portfolio_btn:
    holdings = edited_portfolio[
        edited_portfolio["Symbol"].notna() & (edited_portfolio["Symbol"].astype(str).str.strip() != "")
    ]
    if holdings.empty:
        st.warning("אין אחזקות עם סימול לניתוח.")
    else:
        st.caption("💡 טיפ: לניירות הנסחרים בבורסת ת\"א הוסף סיומת ‎.TA‎ לסימול (לדוגמה: TEVA.TA). קרנות מחקות/נאמנות אינן נתמכות.")
        results = []
        progress = st.progress(0, text="מנתח את התיק...")
        total = len(holdings)
        for i, (_, row) in enumerate(holdings.iterrows()):
            symbol = str(row["Symbol"]).strip().upper()
            # אם הוגדר מדד עוקב - מנתחים אותו במקום הסימול (לקרנות מחקות ישראליות)
            benchmark = str(row.get("Benchmark") or "").strip()
            ticker = benchmark.upper() if benchmark else symbol
            rec = get_quick_recommendation(ticker)
            qty = row.get("Quantity") or 0
            buy = row.get("BuyPrice") or 0
            price = rec["price"]
            pl_pct = ((price - buy) / buy * 100) if (price and buy) else None
            results.append({
                "סימול": symbol,
                "נותח לפי": ticker if benchmark else "—",
                "מחיר נוכחי": price,
                "מחיר קנייה": buy,
                "רווח/הפסד %": round(pl_pct, 2) if pl_pct is not None else None,
                "RSI": rec["rsi"],
                "המלצה": rec["recommendation"],
                "נימוק": rec["reason"],
            })
            progress.progress((i + 1) / total, text=f"מנתח {ticker} ({i+1}/{total})")
        progress.empty()
        results_df = pd.DataFrame(results)
        st.dataframe(results_df, use_container_width=True, hide_index=True)

        buy_count = sum(1 for r in results if "קנייה" in r["המלצה"])
        sell_count = sum(1 for r in results if "מכירה" in r["המלצה"])
        hold_count = sum(1 for r in results if "החזקה" in r["המלצה"])
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("🟢 קנייה/הגדלה", buy_count)
        sc2.metric("🟠 החזקה", hold_count)
        sc3.metric("🔴 צמצום/מכירה", sell_count)

st.divider()

# ==========================================
# יש לי סכום להשקיע - מה לקנות? (סריקת כל השווקים + הצעת תיק)
# ==========================================
st.header("💰 יש לי סכום להשקיע — מה לקנות?")
st.markdown("הזן סכום, והמערכת תסרוק את כל השווקים (ארה\"ב + ת\"א) ותציע איך לפזר אותו לפי עוצמת איתותי הקנייה הנוכחיים.")

@st.cache_data(ttl=1800, show_spinner=False)
def cached_market_scan(scope, min_score):
    return scan_market(get_universe(scope), min_score=min_score, limit=30)

ic1, ic2, ic3 = st.columns([2, 1, 1])
with ic1:
    invest_amount = st.number_input("סכום להשקעה ($)", min_value=0.0, value=1000.0, step=100.0)
with ic2:
    scan_scope = st.selectbox("שווקים", ["US+IL", "US", "IL"], index=0)
with ic3:
    num_picks = st.number_input("כמה מניות לפזר", min_value=1, max_value=20, value=6)

if st.button("🔎 סרוק את השווקים והצע תיק"):
    with st.spinner("סורק עד 120 ניירות בכל השווקים... זה עשוי לקחת עד דקה."):
        hits = cached_market_scan(scan_scope, 4)
    if not hits:
        st.warning("לא נמצאו כרגע איתותי קנייה חזקים בשווקים. נסה שוב מאוחר יותר.")
    else:
        top = hits[:int(num_picks)]
        total_score = sum(h["score"] for h in top) or 1
        rows = []
        for h in top:
            weight = h["score"] / total_score
            alloc = invest_amount * weight
            shares = int(alloc // h["price"]) if h["price"] else 0
            rows.append({
                "סימול": h["symbol"],
                "מחיר": f"${h['price']}",
                "עוצמת איתות": f"{h['score']}/9",
                "הקצאה מומלצת": f"${alloc:,.0f} ({weight*100:.0f}%)",
                "מס' מניות (משוער)": shares,
                "נימוק": ", ".join(h["reasons"]),
            })
        st.success(f"נמצאו {len(hits)} הזדמנויות. הצעת פיזור ל-${invest_amount:,.0f} על פני {len(top)} המובילות:")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption("⚠️ ההקצאה משוקללת לפי עוצמת האיתות הטכני בלבד. זוהי אינה המלצת השקעה — קבל החלטות באחריותך.")

st.divider()

with st.expander("💼 הצג נתוני היסטוריה וטבלאות גולמיות"):
    if symbol and not df.empty:
        st.dataframe(df.tail(20).sort_values(by='Date', ascending=False), use_container_width=True)
