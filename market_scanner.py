"""
סורק שוק רחב - מאתר מניות עם איתות קנייה חזק בכל השווקים.
"""
import logging
from data_engine import fetch_us_data, calculate_technical_indicators

log = logging.getLogger("worker")


def score_buy_signal(df):
    """ניקוד עוצמת איתות הקנייה. ככל שגבוה יותר - ההזדמנות חזקה יותר."""
    last, prev = df.iloc[-1], df.iloc[-2]
    score, reasons = 0, []

    rsi = last['RSI_14']
    if rsi < 30:
        score += 3; reasons.append(f"RSI {rsi:.0f} (מכירת יתר עמוקה)")
    elif rsi < 40:
        score += 1; reasons.append(f"RSI {rsi:.0f} (נמוך)")

    # חציית MACD כלפי מעלה (היפוך מומנטום טרי)
    if prev['MACD'] < prev['MACD_Signal'] and last['MACD'] > last['MACD_Signal']:
        score += 2; reasons.append("חציית MACD כלפי מעלה")

    # פריצה מחדש מעל ממוצע נע 20
    if prev['Close'] < prev['SMA_20'] and last['Close'] > last['SMA_20']:
        score += 2; reasons.append("פריצת ממוצע נע 20")

    # מתחת לרצועת בולינגר התחתונה (פוטנציאל תיקון למעלה)
    if last['Close'] < last['BB_Lower']:
        score += 1; reasons.append("מתחת לבולינגר התחתון")

    # אישור נפח
    if last['Vol_Avg_20'] and last['Volume'] > 1.5 * last['Vol_Avg_20']:
        score += 1; reasons.append("נפח מסחר גבוה")

    return score, reasons


def scan_market(universe, min_score=4, limit=15):
    """סורק את רשימת הניירות ומחזיר את ההזדמנויות החזקות ביותר (ממוינות)."""
    hits = []
    for sym in universe:
        try:
            df = calculate_technical_indicators(fetch_us_data(sym, count=120, period="6mo"))
            if df.empty or len(df) < 30:
                continue
            score, reasons = score_buy_signal(df)
            if score >= min_score:
                hits.append({
                    "symbol": sym,
                    "score": score,
                    "price": round(float(df.iloc[-1]['Close']), 2),
                    "reasons": reasons,
                })
        except Exception:
            continue
    hits.sort(key=lambda h: h["score"], reverse=True)
    log.info("סריקת שוק: נסרקו %d ניירות, נמצאו %d הזדמנויות חזקות", len(universe), len(hits))
    return hits[:limit]
