import os
import logging
import requests
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

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

# -------------------------
# API URLs
# -------------------------
WEATHER_URL = "https://api.openweathermap.org/data/2.5/forecast"
DATA_GOV_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

# -------------------------
# MENU
# -------------------------
MENU = ReplyKeyboardMarkup(
    [
        ["📈 Market Prices", "🌤 Weather"],
        [KeyboardButton("📍 Share Location", request_location=True)],
        ["🌾 Harvest Advice", "🌱 Fertilizer Advice"],
        ["🏛 Government Schemes"],
    ],
    resize_keyboard=True,
)

FARMER_PROFILES = {}

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌾 Smart Farmer Assistant\n\nSelect an option:",
        reply_markup=MENU,
    )

# ================= WEATHER =================

async def weather_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter city name:")
    context.user_data["weather"] = True


async def fetch_weather_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text

    params = {
        "q": city,
        "appid": OPENWEATHER_API,
        "units": "metric",
    }

    r = requests.get(WEATHER_URL, params=params)

    if r.status_code != 200:
        await update.message.reply_text("❌ City not found.")
        return

    data = r.json()

    avg_temp = sum(e["main"]["temp"] for e in data["list"][:8]) / 8
    rain = sum(e.get("rain", {}).get("3h", 0) for e in data["list"][:8])
    humidity = data["list"][0]["main"]["humidity"]
    wind = data["list"][0]["wind"]["speed"]

    await update.message.reply_text(
        f"🌤 Weather in {city.title()}\n\n"
        f"🌡 Avg Temp (24h): {round(avg_temp,1)}°C\n"
        f"🌧 Rain (24h): {round(rain,1)} mm\n"
        f"💧 Humidity: {humidity}%\n"
        f"🌬 Wind Speed: {wind} m/s"
    )

    context.user_data["weather"] = False


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lat = update.message.location.latitude
    lon = update.message.location.longitude

    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API,
        "units": "metric",
    }

    r = requests.get(WEATHER_URL, params=params)

    if r.status_code != 200:
        await update.message.reply_text("Weather fetch failed.")
        return

    data = r.json()

    avg_temp = sum(e["main"]["temp"] for e in data["list"][:8]) / 8
    rain = sum(e.get("rain", {}).get("3h", 0) for e in data["list"][:8])
    humidity = data["list"][0]["main"]["humidity"]

    await update.message.reply_text(
        f"📍 Location Weather\n\n"
        f"🌡 Avg Temp: {round(avg_temp,1)}°C\n"
        f"🌧 Rain: {round(rain,1)} mm\n"
        f"💧 Humidity: {humidity}%"
    )

# ================= MARKET PRICES =================

async def market_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter commodity name (e.g. Wheat):")
    context.user_data["market"] = True


async def fetch_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commodity = update.message.text

    params = {
        "api-key": DATA_GOV_API,
        "format": "json",
        "filters[commodity]": commodity,
        "filters[state]": STATE_NAME,
        "limit": 5,
    }

    r = requests.get(DATA_GOV_URL, params=params)

    if r.status_code != 200:
        await update.message.reply_text("❌ Market API error.")
        return

    data = r.json()

    if "records" not in data or len(data["records"]) == 0:
        await update.message.reply_text("No market data found.")
        return

    reply = f"📈 {commodity.title()} Prices ({STATE_NAME})\n\n"

    for rec in data["records"]:
        reply += (
            f"🏪 Mandi: {rec.get('market','N/A')} APMC\n"
            f"📉 Min: ₹{rec.get('min_price','N/A')}\n"
            f"📈 Max: ₹{rec.get('max_price','N/A')}\n"
            f"💰 Modal: ₹{rec.get('modal_price','N/A')}\n\n"
        )

    await update.message.reply_text(reply)
    context.user_data["market"] = False

# ================= HARVEST ADVICE =================

async def harvest_advice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌾 Harvest Tips:\n\n"
        "• Harvest during dry weather\n"
        "• Avoid harvesting before rainfall\n"
        "• Ensure proper drying before storage\n"
        "• Maintain moisture below recommended level"
    )

# ================= FERTILIZER =================

CROP_NPK = {
    "wheat": (120, 60, 40),
    "rice": (100, 50, 50),
    "maize": (150, 75, 40),
    "cotton": (200, 100, 100),
    "soybean": (30, 60, 40),
    "onion": (100, 50, 50),
    "tomato": (120, 60, 60),
    "potato": (180, 80, 100),
    "sugarcane": (250, 115, 115),
}

async def fertilizer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    FARMER_PROFILES[update.effective_user.id] = {}
    await update.message.reply_text("Enter crop name:")
    context.user_data["fert"] = 1


async def fertilizer_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    step = context.user_data.get("fert")

    if step == 1:
        FARMER_PROFILES[user_id]["crop"] = update.message.text.lower()
        await update.message.reply_text("Enter soil type (loamy/clay/sandy):")
        context.user_data["fert"] = 2

    elif step == 2:
        FARMER_PROFILES[user_id]["soil"] = update.message.text.lower()
        await update.message.reply_text("Enter soil pH:")
        context.user_data["fert"] = 3

    elif step == 3:
        ph = float(update.message.text)
        profile = FARMER_PROFILES[user_id]
        crop = profile["crop"]
        soil = profile["soil"]

        if crop not in CROP_NPK:
            await update.message.reply_text("Crop data not available.")
            context.user_data["fert"] = 0
            return

        N, P, K = CROP_NPK[crop]

        if soil == "sandy":
            N += 10
            K += 10
        elif soil == "clay":
            P += 10

        correction = ""
        if ph < 6:
            correction = "⚠ Apply Lime (soil acidic)"
        elif ph > 7.5:
            correction = "⚠ Apply Gypsum (soil alkaline)"

        await update.message.reply_text(
            f"🌱 Fertilizer Plan for {crop.title()}\n\n"
            f"🧪 Soil Type: {soil.title()}\n"
            f"📊 Soil pH: {ph}\n\n"
            f"Recommended NPK (kg/ha):\n"
            f"🟢 Nitrogen (N): {N}\n"
            f"🔵 Phosphorus (P): {P}\n"
            f"🟣 Potassium (K): {K}\n\n"
            f"{correction}"
        )

        context.user_data["fert"] = 0

# ================= SCHEMES =================

async def schemes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏛 Government Schemes:\n\n"
        "• PM-KISAN\n"
        "• Soil Health Card Scheme\n"
        "• PM Fasal Bima Yojana\n"
        "• eNAM Market"
    )

# ================= ROUTER =================

async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if context.user_data.get("weather"):
        await fetch_weather_city(update, context)
        return

    if context.user_data.get("market"):
        await fetch_market(update, context)
        return

    if context.user_data.get("fert"):
        await fertilizer_flow(update, context)
        return

    if text == "🌤 Weather":
        await weather_city(update, context)

    elif text == "📈 Market Prices":
        await market_prices(update, context)

    elif text == "🌾 Harvest Advice":
        await harvest_advice(update, context)

    elif text == "🌱 Fertilizer Advice":
        await fertilizer_start(update, context)

    elif text == "🏛 Government Schemes":
        await schemes(update, context)

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()