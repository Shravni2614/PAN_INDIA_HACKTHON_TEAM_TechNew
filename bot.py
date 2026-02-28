import os
import logging
import requests
from dotenv import load_dotenv
from rapidfuzz import process
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from collections import defaultdict
from datetime import datetime

# -------------------------
# Load Environment Variables
# -------------------------
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENWEATHER_API = os.getenv("OPENWEATHER_API")
DATA_GOV_API = os.getenv("DATA_GOV_API")
STATE_NAME = os.getenv("STATE_NAME", "Maharashtra")

# -------------------------
# Logging
# -------------------------
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# -------------------------
# API URLs
# -------------------------
WEATHER_URL = "https://api.openweathermap.org/data/2.5/forecast"
DATA_GOV_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

# -------------------------
# Keyboard Menu
# -------------------------
MENU = ReplyKeyboardMarkup(
    [
        ["📈 Market Prices"],
        ["🌤 Weather"],
        ["🌾 Harvest Advice"],
        ["🏛 Government Schemes"],
    ],
    resize_keyboard=True,
)

# -------------------------
# Government Schemes
# -------------------------
GOV_SCHEMES = {
    "PM-KISAN": "Income support of ₹6000 per year to eligible farmer families.",
    "PMFBY": "Pradhan Mantri Fasal Bima Yojana - Crop insurance scheme.",
    "Soil Health Card": "Provides soil nutrient status and fertilizer recommendations.",
    "KCC": "Kisan Credit Card - Easy credit access for farmers.",
    "e-NAM": "National Agriculture Market - Online trading platform for farmers.",
}

# -------------------------
# City Auto-Correction
# -------------------------
def suggest_city(city):
    common_cities = [
        "Mumbai", "Pune", "Nagpur", "Nashik",
        "Delhi", "Bengaluru", "Hyderabad",
        "Chennai", "Kolkata"
    ]
    match = process.extractOne(city, common_cities)
    if match and match[1] > 70:
        return match[0]
    return city

# -------------------------
# Fetch Weather
# -------------------------
def fetch_weather(city: str):
    try:
        params = {
            "q": city,
            "appid": OPENWEATHER_API,
            "units": "metric",
        }
        response = requests.get(WEATHER_URL, params=params, timeout=10)

        if response.status_code != 200:
            logger.error(f"Weather API Error: {response.text}")
            return None

        return response.json()

    except Exception as e:
        logger.error(f"Weather Exception: {e}")
        return None

# -------------------------
# Fetch Market Prices
# -------------------------
def fetch_market_prices():
    try:
        params = {
            "api-key": DATA_GOV_API,
            "format": "json",
            "limit": 1000,
            "filters[state]": STATE_NAME,
        }
        response = requests.get(DATA_GOV_URL, params=params, timeout=10)

        if response.status_code != 200:
            logger.error(response.text)
            return []

        return response.json().get("records", [])

    except Exception as e:
        logger.error(f"Market Exception: {e}")
        return []

# -------------------------
# Start Command
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌾 Welcome to Smart Krishi AI Bot!\nSelect an option:",
        reply_markup=MENU,
    )

# -------------------------
# Market Handler
# -------------------------
async def handle_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    crop = update.message.text.strip()
    records = fetch_market_prices()

    if not records:
        await update.message.reply_text("❌ Unable to fetch market data.")
        return

    commodities = list(set([r["commodity"] for r in records]))
    match = process.extractOne(crop, commodities)

    if not match or match[1] < 70:
        await update.message.reply_text("❌ Crop not found. Try another.")
        return

    best_match = match[0]
    filtered = [r for r in records if r["commodity"] == best_match]

    msg = f"📈 Market Prices for {best_match} ({STATE_NAME})\n\n"

    for item in filtered[:5]:
        msg += (
            f"Market: {item['market']}\n"
            f"Min: ₹{item['min_price']} | "
            f"Max: ₹{item['max_price']} | "
            f"Modal: ₹{item['modal_price']}\n\n"
        )

    await update.message.reply_text(msg)

# -------------------------
# Weather Handler
# -------------------------
async def handle_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = suggest_city(update.message.text.strip())
    data = fetch_weather(city)

    if not data:
        await update.message.reply_text("❌ Weather data unavailable.")
        return

    daily_data = defaultdict(list)

    for entry in data["list"]:
        date = entry["dt_txt"].split(" ")[0]
        daily_data[date].append(entry)

    msg = f"🌤 5-Day Forecast for {city}\n\n"

    for date, entries in list(daily_data.items())[:5]:
        avg_temp = sum(e["main"]["temp"] for e in entries) / len(entries)
        total_rain = sum(e.get("rain", {}).get("3h", 0) for e in entries)

        readable_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d %b %Y")

        msg += (
            f"{readable_date}\n"
            f"Avg Temp: {round(avg_temp,1)}°C\n"
            f"Total Rain: {round(total_rain,1)} mm\n\n"
        )

    await update.message.reply_text(msg)

# -------------------------
# Harvest Advisory
# -------------------------
async def handle_harvest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = suggest_city(update.message.text.strip())
    data = fetch_weather(city)

    if not data:
        await update.message.reply_text("❌ Weather data unavailable.")
        return

    next_48h = data["list"][:16]

    total_rain = sum(e.get("rain", {}).get("3h", 0) for e in next_48h)
    max_temp = max(e["main"]["temp_max"] for e in next_48h)
    avg_humidity = sum(e["main"]["humidity"] for e in next_48h) / len(next_48h)
    max_wind = max(e["wind"]["speed"] for e in next_48h)

    if total_rain > 20:
        advice = "⚠ Heavy rain expected. Postpone harvest."
    elif total_rain > 5:
        advice = "🌦 Light rain possible. Harvest with caution."
    elif max_temp > 36:
        advice = "🌡 High temperature. Harvest early morning or late evening."
    elif avg_humidity > 85:
        advice = "💧 High humidity. Risk of fungal growth. Dry crops properly."
    elif max_wind > 10:
        advice = "🌬 Strong winds expected. Secure harvested crops."
    else:
        advice = "✅ Favorable weather conditions for harvest."

    await update.message.reply_text(f"🌾 Harvest Advisory for {city}\n\n{advice}")

# -------------------------
# Scheme Handler
# -------------------------
async def handle_schemes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🏛 Government Schemes for Farmers\n\n"
    for name, desc in GOV_SCHEMES.items():
        msg += f"• {name}\n{desc}\n\n"
    await update.message.reply_text(msg)

# -------------------------
# Message Router
# -------------------------
async def message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📈 Market Prices":
        await update.message.reply_text("Enter crop name (e.g., Onion):")
        context.user_data["mode"] = "market"

    elif text == "🌤 Weather":
        await update.message.reply_text("Enter city name:")
        context.user_data["mode"] = "weather"

    elif text == "🌾 Harvest Advice":
        await update.message.reply_text("Enter city name:")
        context.user_data["mode"] = "harvest"

    elif text == "🏛 Government Schemes":
        await handle_schemes(update, context)

    else:
        mode = context.user_data.get("mode")

        if mode == "market":
            await handle_market(update, context)
        elif mode == "weather":
            await handle_weather(update, context)
        elif mode == "harvest":
            await handle_harvest(update, context)
        else:
            await update.message.reply_text("Use /start to begin.")

# -------------------------
# Main
# -------------------------
def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("Missing TELEGRAM_TOKEN in .env")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_router))

    print("Bot started successfully.")
    app.run_polling()

if __name__ == "__main__":
    main()