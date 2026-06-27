"""
ניהול תיק השקעות - טעינה ושמירה של אחזקות לקובץ CSV.
"""
import os
import pandas as pd

PORTFOLIO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "portfolio.csv")

COLUMNS = ["Symbol", "Name", "Currency", "Quantity", "BuyPrice", "Benchmark"]


def load_portfolio():
    """טוען את התיק מהקובץ. אם לא קיים - מחזיר תיק ריק עם העמודות הנכונות."""
    if os.path.exists(PORTFOLIO_FILE):
        try:
            df = pd.read_csv(PORTFOLIO_FILE)
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = None
            return df[COLUMNS]
        except Exception:
            pass
    return pd.DataFrame(columns=COLUMNS)


def save_portfolio(df):
    """שומר את התיק לקובץ CSV (UTF-8 עם BOM כדי שעברית תיפתח נכון באקסל)."""
    df = df.copy()
    # ניקוי שורות ריקות (ללא סימול)
    df = df[df["Symbol"].notna() & (df["Symbol"].astype(str).str.strip() != "")]
    df["Symbol"] = df["Symbol"].astype(str).str.strip().str.upper()
    df.to_csv(PORTFOLIO_FILE, index=False, encoding="utf-8-sig")
    return df
