"""
רשימת הניירות לסריקה הרחבה (כל השווקים).
US = מניות גדולות מ-S&P 500 / Nasdaq 100.
IL = מניות ת"א-125 מובילות (סיומת .TA ל-yfinance).
ניתן להרחיב/לצמצם בחופשיות.
"""

US_LARGE_CAP = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "AMD", "NFLX",
    "ADBE", "CRM", "ORCL", "CSCO", "INTC", "QCOM", "TXN", "MU", "AMAT", "LRCX",
    "JPM", "BAC", "WFC", "GS", "MS", "C", "V", "MA", "AXP", "PYPL",
    "JNJ", "UNH", "LLY", "PFE", "MRK", "ABBV", "TMO", "ABT", "DHR", "BMY",
    "XOM", "CVX", "COP", "SLB", "OXY", "PSX", "WMT", "COST", "HD", "LOW",
    "PG", "KO", "PEP", "MCD", "NKE", "SBUX", "DIS", "CMCSA", "T", "VZ",
    "BA", "CAT", "GE", "HON", "UPS", "RTX", "LMT", "DE", "MMM", "UNP",
    "PLTR", "SNOW", "UBER", "ABNB", "COIN", "SHOP", "SQ", "CRWD", "PANW", "DDOG",
    "MRNA", "GILD", "REGN", "VRTX", "ISRG", "NOW", "INTU", "AMGN", "BKNG", "GM",
]

IL_TA125 = [
    "TEVA.TA", "ESLT.TA", "NICE.TA", "POLI.TA", "LUMI.TA", "DSCT.TA", "MZTF.TA",
    "FIBI.TA", "PHOE.TA", "MGDL.TA", "CLIS.TA", "HARL.TA", "ICL.TA", "NVMI.TA",
    "CAMT.TA", "ELTR.TA", "TSEM.TA", "ORA.TA", "STRS.TA", "BEZQ.TA", "PTNR.TA",
    "AZRG.TA", "MLSR.TA", "BIG.TA", "AMOT.TA", "ENLT.TA", "NWMD.TA", "SHOM.TA",
    "FORTY.TA", "DLEKG.TA",
]


def get_universe(scope="US+IL"):
    if scope == "US":
        return list(US_LARGE_CAP)
    if scope == "IL":
        return list(IL_TA125)
    return list(US_LARGE_CAP) + list(IL_TA125)
