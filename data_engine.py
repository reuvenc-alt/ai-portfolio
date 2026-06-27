import os
import json
import smtplib
import datetime as dt
from email.mime.text import MIMEText
import requests
import pandas as pd
import numpy as np
import websocket
import threading
from scipy.stats import norm
from dotenv import load_dotenv

load_dotenv()
finnhub_client = None
if os.getenv('FINNHUB_API_KEY'):
    import finnhub
    finnhub_client = finnhub.Client(api_key=os.getenv('FINNHUB_API_KEY'))

# פונקציה לשליחת התראות לטלפון הנייד (מבוסס מידע חיצוני - Telegram API)
def send_phone_alert(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if token and chat_id and token != "your-telegram-bot-token":
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": message})

# פונקציה לשליחת התראות למייל (Gmail דרך SMTP)
def send_email_alert(subject, message):
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_APP_PASSWORD")
    recipient = os.getenv("EMAIL_RECIPIENT") or sender
    if not sender or not password or password == "your-gmail-app-password":
        print("⚠️ מייל לא נשלח: חסרים EMAIL_SENDER / EMAIL_APP_PASSWORD בקובץ .env")
        return False
    try:
        msg = MIMEText(message, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"⚠️ שגיאה בשליחת מייל: {e}")
        return False

# שליפת כותרות חדשות אחרונות עבור מניה (Finnhub) להזנת ה-AI
def fetch_news(symbol):
    if not finnhub_client:
        return "אין חדשות זמינות."
    try:
        today = dt.date.today()
        week_ago = today - dt.timedelta(days=7)
        news = finnhub_client.company_news(symbol, _from=str(week_ago), to=str(today))
        headlines = [n.get('headline', '') for n in news[:5] if n.get('headline')]
        return " | ".join(headlines) if headlines else "אין חדשות חריגות."
    except Exception:
        return "אין חדשות זמינות."

class AdaptiveSchemaFabric:
    def __init__(self):
        self.expected_schema = {'s': 'symbol', 'p': 'price', 'v': 'volume', 't': 'timestamp'}
        
    def validate_and_adapt(self, incoming_data):
        keys = set(incoming_data.keys())
        if not set(self.expected_schema.keys()).issubset(keys):
            print(f"⚠️ התראת סכמה: חסרים שדות בזרם הנתונים: {keys}")
        return incoming_data

class TransactionCostModel:
    def __init__(self):
        self.spread = 0.01      
        self.commission = 0.005 
        self.slippage = 0.02    
        
    def apply_costs(self, price, action="BUY"):
        cost_per_unit = self.spread + self.commission + self.slippage
        return price + cost_per_unit if action == "BUY" else price - cost_per_unit

class MonteCarloRiskEngine:
    def run_simulation(self, historical_returns, num_simulations=5000, periods=252):
        if len(historical_returns) < 10: return 0, 0, 0
        simulations = np.random.choice(historical_returns, size=(num_simulations, periods), replace=True)
        cumulative_returns = np.prod(1 + simulations, axis=1)
        risk_of_ruin = np.sum(cumulative_returns < 0.5) / num_simulations 
        prob_profitable = np.sum(cumulative_returns > 1.0) / num_simulations
        median_return = np.median(cumulative_returns) - 1
        return risk_of_ruin, prob_profitable, median_return

def on_message(ws, message):
    data = json.loads(message)
    if data.get('type') == 'trade':
        schema_fabric = AdaptiveSchemaFabric()
        cost_model = TransactionCostModel()
        
        for trade in data['data']:
            valid_trade = schema_fabric.validate_and_adapt(trade)
            adjusted_price = cost_model.apply_costs(valid_trade['p'], "BUY")
            # במערכת אמיתית נפעיל כאן לוגיקה ששולחת התראה לטלפון אם המחיר חורג
            # send_phone_alert(f"🚨 חריגת מחיר זוהתה במניית {valid_trade['s']}: מחיר נוכחי {adjusted_price}")

def start_event_driven_stream():
    api_key = os.getenv('FINNHUB_API_KEY')
    if not api_key or api_key == "your-finnhub-api-key": return
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(f"wss://ws.finnhub.io?token={api_key}", on_message=on_message)
    ws.on_open = lambda ws: ws.send('{"type":"subscribe","symbol":"AAPL"}')
    ws.run_forever()

def run_live_data_background():
    threading.Thread(target=start_event_driven_stream, daemon=True).start()

def fetch_us_data(symbol, count=250, period="2y"):
    # מקור נתונים חינמי - yfinance (מחליף את stock_candles החסום של Finnhub)
    import yfinance as yf
    try:
        hist = yf.Ticker(symbol).history(period=period)
    except Exception as e:
        print(f"⚠️ שגיאה בשליפת נתונים עבור {symbol}: {e}")
        return pd.DataFrame()
    if hist is None or hist.empty:
        return pd.DataFrame()
    hist = hist.reset_index()
    df = pd.DataFrame({
        'Date': pd.to_datetime(hist['Date']).dt.tz_localize(None),
        'Open': hist['Open'].values,
        'High': hist['High'].values,
        'Low': hist['Low'].values,
        'Close': hist['Close'].values,
        'Volume': hist['Volume'].values,
    })
    # הסרת שורות ללא מחיר סגירה (yfinance מוסיף לעיתים שורה ריקה ליום הנוכחי)
    df = df.dropna(subset=['Close']).reset_index(drop=True)
    return df.tail(count).reset_index(drop=True)

def calculate_technical_indicators(df):
    if df.empty: return df
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    # רצועות בולינגר (Bollinger Bands)
    std_20 = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['SMA_20'] + 2 * std_20
    df['BB_Lower'] = df['SMA_20'] - 2 * std_20
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI_14'] = 100 - (100 / (1 + rs))
    # MACD + קו איתות
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    # ATR - לתנודתיות וסטופ-לוס דינמי
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR_14'] = true_range.rolling(window=14).mean()
    # ממוצע נפח מסחר - לזיהוי נפח חריג
    df['Vol_Avg_20'] = df['Volume'].rolling(window=20).mean()
    return df

def get_quick_recommendation(symbol):
    """המלצה מהירה מבוססת-אינדיקטורים עבור מניה בודדת (ללא AI, מהיר וחינמי)."""
    df = calculate_technical_indicators(fetch_us_data(symbol, count=200))
    if df.empty or len(df) < 30:
        return {"price": None, "rsi": None, "recommendation": "אין נתונים", "reason": "לא נמצאו נתונים עבור הסימול"}
    last, prev = df.iloc[-1], df.iloc[-2]
    score, reasons = 0, []
    rsi = last['RSI_14']
    if rsi < 30:
        score += 2; reasons.append(f"RSI {rsi:.0f} (מכירת יתר)")
    elif rsi > 70:
        score -= 2; reasons.append(f"RSI {rsi:.0f} (קניית יתר)")
    else:
        reasons.append(f"RSI {rsi:.0f}")
    if last['MACD'] > last['MACD_Signal']:
        score += 1; reasons.append("MACD חיובי")
    else:
        score -= 1; reasons.append("MACD שלילי")
    if last['Close'] > last['SMA_20']:
        score += 1; reasons.append("מעל ממוצע נע 20")
    else:
        score -= 1; reasons.append("מתחת לממוצע נע 20")
    if score >= 2:
        rec = "🟢 קנייה / הגדלה"
    elif score <= -2:
        rec = "🔴 צמצום / מכירה"
    else:
        rec = "🟠 החזקה"
    return {
        "price": round(float(last['Close']), 2),
        "rsi": round(float(rsi), 1),
        "recommendation": rec,
        "reason": ", ".join(reasons),
    }