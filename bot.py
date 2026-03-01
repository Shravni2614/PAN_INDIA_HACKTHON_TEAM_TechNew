import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

# ------------------ Load Environment ------------------
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

WEATHER_URL = os.getenv("WEATHER_URL")
OPENWEATHER_API = os.getenv("OPENWEATHER_API")
DATA_GOV_API = os.getenv("DATA_GOV_API")
STATE_NAME = os.getenv("STATE_NAME", "Maharashtra")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------ Start Command ------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌾 Welcome to Smart Farming AI Bot 🤖\n"
        "Ask me about crops, fertilizer, harvest, weather, or market prices!"
    )

# ------------------ Weather Helper ------------------
def get_weather(city: str):
    if not OPENWEATHER_API or not WEATHER_URL:
        return "Weather API not configured."

    try:
        params = {"q": city, "appid": OPENWEATHER_API, "units": "metric"}
        r = requests.get(WEATHER_URL, params=params, timeout=10)

        if r.status_code == 200:
            data = r.json()

            if "list" not in data:
                return "Weather data format error."

            avg_temp = sum(e["main"]["temp"] for e in data["list"][:8]) / 8
            rain = sum(e.get("rain", {}).get("3h", 0) for e in data["list"][:8])
            humidity = data["list"][0]["main"]["humidity"]
            wind = data["list"][0]["wind"]["speed"]

            return (
                f"🌡 Avg Temp: {round(avg_temp,1)}°C\n"
                f"🌧 Rain: {round(rain,1)} mm\n"
                f"💧 Humidity: {humidity}%\n"
                f"🌬 Wind Speed: {wind} m/s"
            )

        return "Weather data unavailable for this city."

    except Exception as e:
        return f"Weather API error: {e}"

# ------------------ Market Helper ------------------
def get_market_price(commodity: str):
    if not DATA_GOV_API:
        return "Market API not configured."

    try:
        url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

        params = {
            "api-key": DATA_GOV_API,
            "format": "json",
            "limit": 5,
            "filters[state]": STATE_NAME,
            "filters[commodity]": commodity
        }

        r = requests.get(url, params=params, timeout=10)

        if r.status_code == 200:
            records = r.json().get("records", [])

            if not records:
                return f"No market data found for {commodity}."

            msg = f"📈 Market Prices for {commodity.title()} ({STATE_NAME}):\n\n"

            for rec in records:
                msg += (
                    f"🏪 {rec.get('market','N/A')} APMC\n"
                    f"📉 Min: ₹{rec.get('min_price','N/A')} | "
                    f"📈 Max: ₹{rec.get('max_price','N/A')} | "
                    f"💰 Modal: ₹{rec.get('modal_price','N/A')}\n\n"
                )

            return msg

        return "Market data unavailable."

    except Exception as e:
        return f"Market API error: {e}"

# ------------------ AI Response Handler ------------------
async def ai_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.lower()

    # Weather Detection
    if "weather" in user_text:
        city = user_text.split("in")[-1].strip() if "in" in user_text else STATE_NAME
        weather_info = get_weather(city)
        await update.message.reply_text(weather_info)
        return

    # Market Detection
    if "market price" in user_text or "price of" in user_text:
        commodity = user_text.split("of")[-1].strip() if "of" in user_text else None
        if commodity:
            market_info = get_market_price(commodity)
            await update.message.reply_text(market_info)
            return

    # OpenAI Call
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Recommended fast + affordable model
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful Indian farming assistant. "
                        "Give practical, simple advice for farmers "
                        "about crops, fertilizer, irrigation, pests, and harvesting."
                    )
                },
                {"role": "user", "content": user_text}
            ],
            max_tokens=500,
            temperature=0.7,
        )

        reply = response.choices[0].message.content

    except Exception as e:
        reply = f"❌ AI Error: {e}"

    await update.message.reply_text(reply)

# ------------------ Main ------------------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_response))

    print("🌱 Smart Farming AI Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()