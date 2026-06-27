"""
מנוע סריקה רקעי (Background Worker)
-----------------------------------
רץ באופן עצמאי (לא תלוי ב-Streamlit), סורק רשימת מניות במרווחי זמן קבועים,
מחשב אינדיקטורים, מפעיל ניתוח AI ושולח התראות למייל כאשר מזוהה איתות.

הרצה ידנית:   python worker.py
הרצה ברקע:    דרך Windows Task Scheduler (ראה run_worker.bat)
"""
import os
import json
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

import sys
from data_engine import (
    fetch_us_data,
    calculate_technical_indicators,
    fetch_news,
    send_email_alert,
    get_quick_recommendation,
)
from ai_core import analyze_stock_with_ai
from market_scanner import scan_market
from universe import get_universe
from portfolio import load_portfolio

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WATCHLIST = [s.strip().upper() for s in os.getenv("WATCHLIST", "AAPL,MSFT,TSLA,NVDA,TEVA").split(",") if s.strip()]
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL_SECONDS", "1800"))  # ברירת מחדל: 30 דקות
STATE_FILE = os.path.join(BASE_DIR, "alert_state.json")
LOG_FILE = os.path.join(BASE_DIR, "worker.log")

# רישום לקובץ + מסך — כך אפשר לוודא שהמנוע רץ ברקע (פתח את worker.log)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
)
log = logging.getLogger("worker")


def load_state():
    """טוען את מצב ההתראות האחרון כדי לא לשלוח התראה זהה פעמיים."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def evaluate_signals(df):
    """מחזיר רשימת איתותים לפי חוקים טכניים. כל איתות = (כיוון, הסבר)."""
    last = df.iloc[-1]
    prev = df.iloc[-2]
    signals = []

    # RSI - מכירת/קניית יתר
    if last['RSI_14'] < 30:
        signals.append(("BUY", f"RSI נמוך ({last['RSI_14']:.1f}) — מצב מכירת יתר"))
    elif last['RSI_14'] > 70:
        signals.append(("SELL", f"RSI גבוה ({last['RSI_14']:.1f}) — מצב קניית יתר"))

    # חציית MACD מול קו האיתות
    if prev['MACD'] < prev['MACD_Signal'] and last['MACD'] > last['MACD_Signal']:
        signals.append(("BUY", "חציית MACD כלפי מעלה — מומנטום חיובי"))
    elif prev['MACD'] > prev['MACD_Signal'] and last['MACD'] < last['MACD_Signal']:
        signals.append(("SELL", "חציית MACD כלפי מטה — מומנטום שלילי"))

    # רצועות בולינגר
    if last['Close'] < last['BB_Lower']:
        signals.append(("BUY", "המחיר מתחת לרצועת בולינגר התחתונה"))
    elif last['Close'] > last['BB_Upper']:
        signals.append(("SELL", "המחיר מעל רצועת בולינגר העליונה"))

    # נפח מסחר חריג (מעל פי 2 מהממוצע) — מחזק כל איתות אחר
    if signals and last['Volume'] > 2 * last['Vol_Avg_20']:
        signals.append(("INFO", "נפח מסחר חריג (מעל פי 2 מהממוצע)"))

    return signals


def signal_fingerprint(signals):
    """טביעת אצבע ייחודית לקבוצת איתותים — לזיהוי כפילויות."""
    return ";".join(sorted(s[1] for s in signals))


def build_email_body(symbol, df, signals, ai_result):
    last = df.iloc[-1]
    lines = [
        f"🚨 התראת מסחר עבור {symbol}",
        f"תאריך: {datetime.now():%Y-%m-%d %H:%M}",
        "",
        f"מחיר נוכחי: ${last['Close']:.2f}",
        f"RSI(14): {last['RSI_14']:.1f}  |  MACD: {last['MACD']:.3f}  |  ATR(14): {last['ATR_14']:.2f}",
        "",
        "── איתותים טכניים ──",
    ]
    for direction, reason in signals:
        lines.append(f"  • [{direction}] {reason}")

    lines += ["", "── ניתוח AI ──"]
    if isinstance(ai_result, dict):
        for key in ("Action", "Confidence", "Target_Price", "Stop_Loss", "Reasoning"):
            if key in ai_result:
                lines.append(f"  {key}: {ai_result[key]}")
    else:
        lines.append(f"  {ai_result}")

    lines += ["", "—", "נשלח אוטומטית ע\"י מנהל תיק השקעות AI-Native."]
    return "\n".join(lines)


def scan_once(state):
    """מבצע סבב סריקה יחיד על כל המניות ברשימה."""
    log.info("מתחיל סבב סריקה על %d מניות...", len(WATCHLIST))
    for symbol in WATCHLIST:
        try:
            df = calculate_technical_indicators(fetch_us_data(symbol, count=250))
            if df.empty or len(df) < 30:
                log.info("  %s: אין מספיק נתונים, מדלג.", symbol)
                continue

            signals = evaluate_signals(df)
            actionable = [s for s in signals if s[0] in ("BUY", "SELL")]
            if not actionable:
                log.info("  %s: אין איתות.", symbol)
                continue

            fingerprint = signal_fingerprint(signals)
            if state.get(symbol) == fingerprint:
                log.info("  %s: איתות זהה כבר נשלח, מדלג.", symbol)
                continue

            # ניתוח AI עם נתונים טכניים + חדשות אמיתיות
            tech_snapshot = str(df[['Close', 'RSI_14', 'MACD', 'ATR_14']].tail(1).to_dict())
            news = fetch_news(symbol)
            ai_result = analyze_stock_with_ai(symbol, tech_snapshot, news)

            body = build_email_body(symbol, df, signals, ai_result)
            directions = "/".join(sorted({s[0] for s in actionable}))
            sent = send_email_alert(f"🚨 {symbol}: התראת {directions}", body)

            if sent:
                state[symbol] = fingerprint
                save_state(state)
                log.info("  %s: ✅ התראה נשלחה למייל (%s).", symbol, directions)
            else:
                log.warning("  %s: זוהה איתות אך המייל לא נשלח (בדוק הגדרות .env).", symbol)

        except Exception:
            log.exception("  %s: ❌ שגיאה", symbol)


def run_market_scan():
    """סורק את כל השווקים ושולח מייל עם הזדמנויות הקנייה החזקות ביותר."""
    scope = os.getenv("MARKET_SCOPE", "US+IL")
    min_score = int(os.getenv("MARKET_MIN_SCORE", "4"))
    universe = get_universe(scope)
    hits = scan_market(universe, min_score=min_score, limit=15)
    if not hits:
        log.info("סריקת שוק: לא נמצאו הזדמנויות חזקות הפעם.")
        return
    lines = [f"🌍 הזדמנויות קנייה חזקות בשווקים ({datetime.now():%Y-%m-%d %H:%M})", ""]
    for h in hits:
        lines.append(f"⭐ {h['symbol']}  |  מחיר ${h['price']}  |  עוצמה {h['score']}/9")
        lines.append(f"    {', '.join(h['reasons'])}")
        lines.append("")
    lines.append("— נשלח אוטומטית ע\"י סורק השוק AI-Native.")
    send_email_alert(f"🌍 {len(hits)} הזדמנויות קנייה חזקות בשווקים", "\n".join(lines))
    log.info("סריקת שוק: נשלח מייל עם %d הזדמנויות.", len(hits))


def analyze_my_portfolio():
    """מנתח כל אחזקה בתיק ומסווג למכירה / החזקה / הגדלה."""
    df = load_portfolio()
    sell, hold, buy = [], [], []
    for _, h in df.iterrows():
        sym = str(h.get("Symbol") or "").strip().upper()
        if not sym or sym == "NAN":
            continue
        bm = str(h.get("Benchmark") or "").strip()
        ticker = bm.upper() if bm else sym
        rec = get_quick_recommendation(ticker)
        item = (sym, ticker, rec)
        r = rec["recommendation"]
        if "מכירה" in r:
            sell.append(item)
        elif "קנייה" in r:
            buy.append(item)
        else:
            hold.append(item)
    return sell, hold, buy


def run_portfolio_report():
    """שולח מייל סיכום: מה למכור, מה להחזיק, מה להגדיל בתיק."""
    sell, hold, buy = analyze_my_portfolio()
    if not (sell or hold or buy):
        log.info("דוח תיק: אין אחזקות לניתוח.")
        return
    lines = [f"📋 ניתוח התיק שלך ({datetime.now():%Y-%m-%d %H:%M})", ""]

    def section(title, items):
        out = [title]
        if not items:
            out.append("    (אין)")
        for sym, ticker, rec in items:
            via = f" [לפי {ticker}]" if ticker != sym else ""
            out.append(f"    • {sym}{via}: {rec['reason']}")
        out.append("")
        return out

    lines += section("🔴 לשקול מכירה / צמצום:", sell)
    lines += section("🟢 לשקול הגדלה:", buy)
    lines += section("🟠 להחזיק:", hold)
    lines.append("— נשלח אוטומטית ע\"י מנהל התיק AI-Native.")
    send_email_alert(f"📋 ניתוח התיק: {len(sell)} למכירה, {len(buy)} להגדלה, {len(hold)} להחזקה",
                     "\n".join(lines))
    log.info("דוח תיק: נשלח (מכירה=%d, הגדלה=%d, החזקה=%d)", len(sell), len(buy), len(hold))


def run_once(state):
    """סבב מלא יחיד: התראות מעקב + סריקת שוק + דוח תיק. מתאים לתזמון בענן."""
    scan_once(state)
    run_market_scan()
    run_portfolio_report()


def main():
    log.info("=" * 40)
    log.info("🤖 מנוע הסריקה AI-Native הופעל")
    log.info("רשימת מעקב: %s", ", ".join(WATCHLIST))
    log.info("=" * 40)
    state = load_state()

    # מצב ריצה-יחידה (לשימוש ב-GitHub Actions / משימה מתוזמנת): סורק פעם אחת ויוצא
    if len(sys.argv) > 1 and sys.argv[1] == "once":
        log.info("מצב ריצה יחידה (once)")
        run_once(state)
        log.info("סבב יחיד הושלם.")
        return

    # מצב רציף (מחשב מקומי): התראות מעקב כל מרווח זמן
    log.info("מצב רציף - מרווח סריקה: %d דקות", SCAN_INTERVAL // 60)
    while True:
        try:
            scan_once(state)
        except Exception:
            log.exception("שגיאה כללית בסבב הסריקה")
        log.info("ממתין %d דקות לסבב הבא...", SCAN_INTERVAL // 60)
        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    main()
