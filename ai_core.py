import os
import json
from dotenv import load_dotenv

load_dotenv()

def analyze_stock_with_ai(symbol, technical_data, news_headlines):
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == "sk-your-openai-api-key":
        return {"Action": "DEMO", "Confidence": "90%", "Reasoning": "אנא הזן מפתח OpenAI בקובץ .env כדי לראות ניתוח אמיתי."}
        
    import openai
    client = openai.OpenAI(api_key=api_key)
    
    system_prompt = """
    You are an expert AI financial analyst. Analyze the provided technical data and news.
    Return ONLY a valid JSON object with:
    - "Action": One of [BUY NOW, BUY, ACCUMULATE, HOLD, REDUCE, SELL, AVOID]
    - "Target_Price": Float
    - "Stop_Loss": Float
    - "Confidence": String percentage (e.g., "85%")
    - "Reasoning": A detailed explanation in Hebrew (Explainability-First principle).
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Symbol: {symbol}\nTechnicals: {technical_data}\nNews: {news_headlines}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"Action": "ERROR", "Reasoning": f"שגיאה בניתוח: {str(e)}"}