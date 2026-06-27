# מדריך פריסה לענן 🚀

המטרה: דשבורד שנגיש מהנייד בכל מקום + סורק שמתריע במייל בלי שהמחשב דלוק.

| רכיב | היכן רץ | מה הוא עושה |
|------|---------|-------------|
| 📊 דשבורד (app.py) | **Streamlit Cloud** | צפייה מהנייד/מחשב בכל זמן |
| 🔔 סורק (worker.py once) | **GitHub Actions** | התראות מייל בתזמון (שוק + תיק) |

---

## שלב 0: התקנות והכנה

1. התקן **Git**: https://git-scm.com/download/win  (או GitHub Desktop: https://desktop.github.com)
2. צור חשבון ב-https://github.com אם אין לך.
3. ⚠️ **חשוב**: צור מאגר **פרטי (Private)** — הקובץ portfolio.csv מכיל את האחזקות שלך.

## שלב 1: העלאה ל-GitHub

```powershell
cd E:\AI_Portfolio_Hebrew
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<USERNAME>/<REPO>.git
git push -u origin main
```

✅ קובץ `.gitignore` כבר דואג ש-`.env` (המפתחות שלך) **לא** יועלה.

## שלב 2: דשבורד ב-Streamlit Cloud (גישה מהנייד)

1. היכנס ל-https://share.streamlit.io עם חשבון GitHub.
2. **New app** → בחר את המאגר, ענף `main`, קובץ `app.py`.
3. **Advanced settings → Secrets** → הדבק (עם ערכים אמיתיים):
   ```toml
   OPENAI_API_KEY = "sk-..."
   FINNHUB_API_KEY = "..."
   EMAIL_SENDER = "you@gmail.com"
   EMAIL_APP_PASSWORD = "סיסמת-האפליקציה-16-תווים"
   EMAIL_RECIPIENT = "you@gmail.com"
   ```
4. **Deploy**. תוך דקה תקבל כתובת `https://<your-app>.streamlit.app` — פתח אותה בנייד והוסף למסך הבית.

## שלב 3: סורק אוטומטי ב-GitHub Actions (התראות)

1. במאגר ב-GitHub: **Settings → Secrets and variables → Actions → New repository secret**.
2. הוסף כל אחד מאלה כ-secret נפרד:
   `OPENAI_API_KEY`, `FINNHUB_API_KEY`, `EMAIL_SENDER`, `EMAIL_APP_PASSWORD`, `EMAIL_RECIPIENT`, `WATCHLIST`
3. זהו! הקובץ `.github/workflows/scan.yml` כבר מוגדר. הסורק ירוץ אוטומטית פעמיים ביום בימי חול.
4. להרצה ידנית/בדיקה: לשונית **Actions → AI Portfolio Scanner → Run workflow**.

---

## תזכורות אבטחה 🔒
- ה-App Password של Gmail **חובה** (16 תווים) — לא הסיסמה הרגילה.
- מומלץ לסובב את מפתח ה-OpenAI (נחשף בעבר).
- המאגר חייב להיות **פרטי** בגלל portfolio.csv.
