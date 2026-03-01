# bot.py
import os
import requests
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# Import local data manager
from local_data_manager import market_data

# ---------------------------
# Setup Logging
# ---------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------------------
# Load ENV variables
# ---------------------------
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
DATA_GOV_API_KEY = os.getenv("DATA_GOV_API_KEY")

# ---------------------------
# Conversation States
# ---------------------------
MENU, MARKET, WEATHER, HARVEST, LOCATION_WEATHER, MARKET_STATE = range(6)

# ---------------------------
# Helper Functions
# ---------------------------
def validate_env():
    """Check if all required environment variables are set"""
    required_vars = {
        'BOT_TOKEN': BOT_TOKEN,
        'WEATHER_API_KEY': WEATHER_API_KEY,
        'DATA_GOV_API_KEY': DATA_GOV_API_KEY
    }
    
    missing = [var for var, value in required_vars.items() if not value]
    
    if missing:
        logger.error(f"Missing environment variables: {', '.join(missing)}")
        return False
    return True

def format_date(date_str):
    """Convert YYYY-MM-DD to DD MMM YYYY format"""
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    try:
        year = date_str[0:4]
        month = int(date_str[5:7]) - 1
        day = date_str[8:10]
        return f"{day} {months[month]} {year}"
    except:
        return date_str

def get_weather_emoji(description):
    """Get emoji for weather description"""
    desc = description.lower()
    if 'clear' in desc or 'sunny' in desc:
        return '☀️'
    elif 'cloud' in desc:
        return '☁️'
    elif 'rain' in desc:
        return '🌧️'
    elif 'thunder' in desc:
        return '⛈️'
    elif 'snow' in desc:
        return '❄️'
    elif 'mist' in desc or 'fog' in desc:
        return '🌫️'
    else:
        return '🌤️'

# ---------------------------
# Start Command
# ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    # Check if bot is properly configured
    if not validate_env():
        await update.message.reply_text(
            "⚠️ Bot is not properly configured. Please contact administrator."
        )
        return ConversationHandler.END
    
    # Store user data
    context.user_data['state'] = 'Maharashtra'  # Default state
    
    keyboard = [
        ["📈 Market Prices"],
        ["🌤 Weather", "📍 Share Location"],
        ["🌾 Harvest Advice"],
        ["❌ Cancel"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "🌾 *Welcome to Smart Krishi AI Bot!*\n\n"
        "I can help you with:\n"
        "• Current market prices for crops\n"
        "• Weather forecasts\n"
        "• Harvesting advice based on weather\n\n"
        "*How to use:*\n"
        "• Tap the buttons below to select an option\n"
        "• For weather, you can type a city name OR share your location\n"
        "• Type /cancel anytime to stop\n\n"
        "Please select an option:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return MENU

# ---------------------------
# Cancel Command
# ---------------------------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the current operation"""
    await update.message.reply_text(
        "❌ Operation cancelled. Type /start to begin again.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ---------------------------
# Show Menu
# ---------------------------
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu"""
    keyboard = [
        ["📈 Market Prices"],
        ["🌤 Weather", "📍 Share Location"],
        ["🌾 Harvest Advice"],
        ["❌ Cancel"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Main Menu - Please select an option:",
        reply_markup=reply_markup
    )
    return MENU

# ---------------------------
# Menu Handler
# ---------------------------
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu selections"""
    text = update.message.text

    # Handle special options
    if text == "📋 Show All Crops" or text == "📊 View All Crops":
        return await show_all_crops(update, context)
    
    elif text == "🌍 Try Live API":
        if 'last_crop' in context.user_data and 'last_state' in context.user_data:
            crop = context.user_data['last_crop']
            state = context.user_data['last_state']
            loading_msg = await update.message.reply_text(f"🌍 Trying live API for {crop}...")
            await try_api_market_price(update, context, crop, state, loading_msg)
        else:
            await update.message.reply_text("Please search for a crop first.")
        return MENU
    
    elif text == "💾 Save to Local Database":
        return await save_api_to_local(update, context)
    
    elif text == "🔍 Search Another Crop":
        await update.message.reply_text("Enter crop name:")
        return MARKET

    if text == "📈 Market Prices":
        keyboard = [["Maharashtra", "Uttar Pradesh"], ["Punjab", "Karnataka"], ["🔙 Back to Menu"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "Select your state:",
            reply_markup=reply_markup
        )
        return MARKET_STATE

    elif text == "🌤 Weather":
        await update.message.reply_text(
            "Enter city name (e.g., Mumbai, Pune, Delhi):\n\n"
            "Or use 📍 Share Location button for automatic detection."
        )
        return WEATHER

    elif text == "📍 Share Location":
        await update.message.reply_text(
            "Please share your location using the attachment button 📎",
            reply_markup=ReplyKeyboardMarkup([["🔙 Back to Menu"]], resize_keyboard=True)
        )
        return LOCATION_WEATHER

    elif text == "🌾 Harvest Advice":
        await update.message.reply_text(
            "Enter your city name for harvest advice:"
        )
        return HARVEST

    elif text == "🔙 Back to Menu" or text == "❌ Cancel":
        return await show_menu(update, context)

    # If message doesn't match any option
    await update.message.reply_text(
        "Please select a valid option from the menu."
    )
    return MENU

# ---------------------------
# Market State Selection
# ---------------------------
async def market_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle state selection for market prices"""
    text = update.message.text
    
    if text == "🔙 Back to Menu":
        return await show_menu(update, context)
    
    # Save selected state
    context.user_data['market_state'] = text
    
    await update.message.reply_text(
        f"Selected state: {text}\n\n"
        f"Enter crop name (e.g., Onion, Potato, Tomato, Wheat, Rice):\n\n"
        f"*Available crops:* {', '.join(market_data.get_all_crops()[:5])}...",
        parse_mode='Markdown'
    )
    return MARKET

# ---------------------------
# Try API Market Price
# ---------------------------
async def try_api_market_price(update: Update, context: ContextTypes.DEFAULT_TYPE, crop, state, loading_msg=None):
    """Try to fetch from API"""
    
    url = (
        "https://api.data.gov.in/resource/"
        "9ef84268-d588-465a-a308-a864a43d0070"
        f"?api-key={DATA_GOV_API_KEY}"
        "&format=json"
        f"&filters[commodity]={crop}"
        f"&filters[state]={state}"
        "&limit=10"
    )
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "records" in data and data["records"]:
            if loading_msg:
                await loading_msg.delete()
            
            message = f"🌍 *Live Market Prices for {crop}*\n"
            message += f"📍 State: {state}\n"
            message += f"📊 Data from data.gov.in API\n\n"
            
            for record in data["records"][:7]:
                message += (
                    f"🏪 *{record.get('market', 'Unknown')}*\n"
                    f"Min: ₹{record.get('min_price', 'N/A')}\n"
                    f"Max: ₹{record.get('max_price', 'N/A')}\n"
                    f"Modal: ₹{record.get('modal_price', 'N/A')}\n"
                    f"📅 {record.get('arrival_date', 'Recent')}\n\n"
                )
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
            # Offer to save this data locally
            keyboard = [
                ["💾 Save to Local Database"],
                ["🔍 Search Another"],
                ["🔙 Back to Menu"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                "Would you like to save this data for offline use?",
                reply_markup=reply_markup
            )
            
            # Store API results for potential saving
            context.user_data['api_results'] = {
                'crop': crop,
                'state': state,
                'records': data["records"]
            }
            
            return True
    
    except Exception as e:
        logger.error(f"API error: {e}")
        if loading_msg:
            await loading_msg.edit_text(f"❌ API error: {str(e)[:50]}")
    
    return False

# ---------------------------
# Market Prices (Hybrid)
# ---------------------------
async def market_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hybrid market price handler - uses local data first, then API fallback"""
    crop = update.message.text.strip().title()
    state = context.user_data.get('market_state', 'Maharashtra')
    
    # Show loading message
    loading_msg = await update.message.reply_text(
        f"🔍 Looking up {crop} prices in {state}...\n"
        f"(Checking local database first)"
    )
    
    # STEP 1: Try local data first
    local_results = market_data.query(crop, state)
    
    if local_results:
        await loading_msg.delete()
        
        # Determine data source message
        source_msg = {
            "sample": "📋 Sample Data (For Demo)",
            "local": "💾 Local Dataset"
        }.get(market_data.data_source, "📊 Market Data")
        
        # Format the message
        message = f"📈 *Market Prices for {crop}*\n"
        message += f"📍 State: {state}\n"
        message += f"{source_msg}\n"
        message += f"🕐 Last Updated: {market_data.last_updated}\n\n"
        
        # Group by market and show top results
        for record in local_results[:7]:  # Show up to 7 markets
            message += (
                f"🏪 *{record['market']}*\n"
                f"Min: ₹{record['min_price']}\n"
                f"Max: ₹{record['max_price']}\n"
                f"Modal: ₹{record['modal_price']}\n"
                f"📅 {record.get('arrival_date', 'Recent')}\n\n"
            )
        
        # Add source attribution
        message += "_Data Source: data.gov.in (AGMARKNET)_"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
        # Offer options for next action
        keyboard = [
            ["🔍 Search Another Crop"],
            ["📊 View All Crops"],
            ["🌍 Try Live API"],
            ["🔙 Back to Menu"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "What would you like to do next?",
            reply_markup=reply_markup
        )
        
        # Store context for next actions
        context.user_data['last_crop'] = crop
        context.user_data['last_state'] = state
        
        return MENU
    
    # STEP 2: If local data not found, try API
    await loading_msg.edit_text(
        f"🔄 {crop} not found in local database.\n"
        f"Trying live API..."
    )
    
    # Try API
    api_success = await try_api_market_price(update, context, crop, state, loading_msg)
    
    if not api_success:
        await loading_msg.delete()
        
        # Show helpful suggestions
        available_crops = market_data.get_all_crops()
        available_states = market_data.get_all_states(crop) if crop in market_data.data else []
        
        message = f"❌ No data found for '{crop}' in {state}.\n\n"
        
        if available_crops:
            message += f"*Available crops in database:*\n"
            message += ", ".join([f"`{c}`" for c in available_crops[:10]])
            message += "\n\n"
        
        if crop in market_data.data:
            message += f"*Available states for {crop}:*\n"
            message += ", ".join([f"`{s}`" for s in available_states])
            message += "\n\n"
        
        message += "Try selecting from the menu below:"
        
        keyboard = [
            ["📋 Show All Crops"],
            ["🌍 Try Live API"],
            ["🔙 Back to Menu"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
    
    return MENU

# ---------------------------
# Show All Crops
# ---------------------------
async def show_all_crops(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all available crops in local database"""
    
    crops = market_data.get_all_crops()
    
    if not crops:
        await update.message.reply_text("No crops available in database.")
        return MENU
    
    # Create keyboard with crop buttons
    keyboard = []
    row = []
    for i, crop in enumerate(crops, 1):
        row.append(crop)
        if i % 3 == 0:  # 3 crops per row
            keyboard.append(row)
            row = []
    if row:  # Add remaining crops
        keyboard.append(row)
    
    keyboard.append(["🔙 Back to Menu"])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"📋 *Available Crops ({len(crops)} total)*\n\n"
        f"Select a crop to see available states:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    
    return MARKET  # Return to market state for crop selection

# ---------------------------
# Save API to Local
# ---------------------------
async def save_api_to_local(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save API results to local database"""
    
    if 'api_results' not in context.user_data:
        await update.message.reply_text("No API results to save.")
        return MENU
    
    results = context.user_data['api_results']
    crop = results['crop']
    state = results['state']
    records = results['records']
    
    # Add to local data structure
    if crop not in market_data.data:
        market_data.data[crop] = {}
    
    if state not in market_data.data[crop]:
        market_data.data[crop][state] = []
    
    # Add new records (avoid duplicates)
    existing_markets = {r['market'] for r in market_data.data[crop][state]}
    new_records = [r for r in records if r.get('market') not in existing_markets]
    
    if new_records:
        market_data.data[crop][state].extend(new_records)
        # Save to file
        filename = market_data.save_to_file()
        
        await update.message.reply_text(
            f"✅ Saved {len(new_records)} new records for {crop} in {state}!\n"
            f"📁 File: {filename}"
        )
    else:
        await update.message.reply_text("No new records to save (already in database).")
    
    return MENU

# ---------------------------
# Weather Forecast (by City)
# ---------------------------
async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch and display weather forecast by city name"""
    city = update.message.text.strip().title()
    
    if city == "🔙 Back to Menu":
        return await show_menu(update, context)

    url = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?q={city}&appid={WEATHER_API_KEY}&units=metric"
    )

    try:
        loading_msg = await update.message.reply_text(f"🌤 Fetching weather for {city}...")
        
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("cod") != "200":
            await loading_msg.delete()
            error_msg = data.get("message", "City not found")
            await update.message.reply_text(
                f"❌ Weather data unavailable: {error_msg}\n\n"
                f"Try:\n"
                f"• Checking spelling\n"
                f"• Using a nearby city\n"
                f"• Sharing your location instead"
            )
            return ConversationHandler.END

        # Get current weather
        current = data["list"][0]
        current_temp = current["main"]["temp"]
        current_desc = current["weather"][0]["description"]
        current_humidity = current["main"]["humidity"]
        current_wind = current["wind"]["speed"]

        # Process 5-day forecast
        daily_data = {}
        for entry in data["list"]:
            date = entry["dt_txt"].split(" ")[0]
            if date not in daily_data:
                daily_data[date] = {
                    "temps": [],
                    "humidity": [],
                    "rain": 0,
                    "weather": []
                }
            
            daily_data[date]["temps"].append(entry["main"]["temp"])
            daily_data[date]["humidity"].append(entry["main"]["humidity"])
            daily_data[date]["rain"] += entry.get("rain", {}).get("3h", 0)
            daily_data[date]["weather"].append(entry["weather"][0]["description"])

        await loading_msg.delete()

        # Send current weather
        current_msg = (
            f"🌤 *Current Weather in {city}*\n"
            f"{get_weather_emoji(current_desc)} {current_desc.capitalize()}\n"
            f"🌡 Temperature: {current_temp}°C\n"
            f"💧 Humidity: {current_humidity}%\n"
            f"💨 Wind: {current_wind} m/s\n\n"
            f"*5-Day Forecast:*\n"
        )
        await update.message.reply_text(current_msg, parse_mode='Markdown')

        # Send forecast day by day
        for date, values in list(daily_data.items())[:5]:
            avg_temp = round(sum(values["temps"]) / len(values["temps"]), 1)
            avg_humidity = round(sum(values["humidity"]) / len(values["humidity"]))
            total_rain = round(values["rain"], 1)
            
            # Get most common weather description
            weather_counts = {}
            for desc in values["weather"]:
                weather_counts[desc] = weather_counts.get(desc, 0) + 1
            common_weather = max(weather_counts, key=weather_counts.get)

            day_msg = (
                f"📅 *{format_date(date)}*\n"
                f"{get_weather_emoji(common_weather)} {common_weather.capitalize()}\n"
                f"🌡 {avg_temp}°C | 💧 {avg_humidity}%\n"
                f"☔ Rain: {total_rain}mm\n"
            )
            await update.message.reply_text(day_msg, parse_mode='Markdown')

        # Ask for next action
        keyboard = [["🌤 Another City"], ["📍 Share Location"], ["🔙 Back to Menu"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "What would you like to do next?",
            reply_markup=reply_markup
        )
        return MENU

    except requests.Timeout:
        await update.message.reply_text("❌ Request timed out. Please try again.")
    except Exception as e:
        logger.error(f"Error in weather: {e}")
        await update.message.reply_text("❌ Error fetching weather data.")
    
    return ConversationHandler.END

# ---------------------------
# Weather by Location
# ---------------------------
async def weather_by_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch weather forecast using location coordinates"""
    
    if update.message.text == "🔙 Back to Menu":
        return await show_menu(update, context)
    
    # Check if we actually received a location
    if not update.message.location:
        await update.message.reply_text(
            "❌ Please share your location using the attachment button 📎"
        )
        return LOCATION_WEATHER
    
    location = update.message.location
    lat, lon = location.latitude, location.longitude

    # Show loading
    loading_msg = await update.message.reply_text("📍 Getting weather for your location...")

    try:
        # First get city name from coordinates (reverse geocoding)
        geo_url = (
            f"http://api.openweathermap.org/geo/1.0/reverse"
            f"?lat={lat}&lon={lon}&limit=1&appid={WEATHER_API_KEY}"
        )
        
        geo_response = requests.get(geo_url, timeout=10)
        geo_data = geo_response.json()
        
        if geo_data and len(geo_data) > 0:
            city = geo_data[0].get('name', 'Unknown location')
            state = geo_data[0].get('state', '')
            country = geo_data[0].get('country', '')
            location_name = f"{city}, {state}, {country}" if state else f"{city}, {country}"
        else:
            location_name = f"Location (Lat: {lat:.2f}, Lon: {lon:.2f})"

        # Get weather forecast
        weather_url = (
            f"https://api.openweathermap.org/data/2.5/forecast"
            f"?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
        )
        
        weather_response = requests.get(weather_url, timeout=10)
        data = weather_response.json()

        if data.get("cod") != "200":
            await loading_msg.delete()
            await update.message.reply_text("❌ Weather data unavailable for this location.")
            return ConversationHandler.END

        # Get current weather
        current = data["list"][0]
        current_temp = current["main"]["temp"]
        current_desc = current["weather"][0]["description"]
        current_humidity = current["main"]["humidity"]

        # Process 3-day forecast (simpler for location-based)
        daily_data = {}
        for entry in data["list"][:8]:  # First 24 hours (8 * 3-hour intervals)
            date = entry["dt_txt"].split(" ")[0]
            if date not in daily_data:
                daily_data[date] = {
                    "temps": [],
                    "rain": 0,
                    "weather": []
                }
            
            daily_data[date]["temps"].append(entry["main"]["temp"])
            daily_data[date]["rain"] += entry.get("rain", {}).get("3h", 0)
            daily_data[date]["weather"].append(entry["weather"][0]["description"])

        await loading_msg.delete()

        # Send weather info
        weather_msg = (
            f"📍 *Weather at your location*\n"
            f"📌 {location_name}\n\n"
            f"*Current Conditions:*\n"
            f"{get_weather_emoji(current_desc)} {current_desc.capitalize()}\n"
            f"🌡 Temperature: {current_temp}°C\n"
            f"💧 Humidity: {current_humidity}%\n\n"
            f"*Next 24 hours:*\n"
        )
        await update.message.reply_text(weather_msg, parse_mode='Markdown')

        # Show next 24 hours forecast
        for date, values in list(daily_data.items())[:2]:  # Today and tomorrow
            avg_temp = round(sum(values["temps"]) / len(values["temps"]), 1)
            total_rain = round(values["rain"], 1)
            
            # Get most common weather
            weather_counts = {}
            for desc in values["weather"]:
                weather_counts[desc] = weather_counts.get(desc, 0) + 1
            common_weather = max(weather_counts, key=weather_counts.get)

            day_msg = (
                f"📅 *{format_date(date)}*\n"
                f"{get_weather_emoji(common_weather)} {common_weather.capitalize()}\n"
                f"🌡 Avg: {avg_temp}°C | ☔ {total_rain}mm\n"
            )
            await update.message.reply_text(day_msg, parse_mode='Markdown')

        # Ask for next action
        keyboard = [["🌤 Weather by City"], ["📍 Share Location Again"], ["🔙 Back to Menu"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "What would you like to do next?",
            reply_markup=reply_markup
        )
        return MENU

    except Exception as e:
        logger.error(f"Error in location weather: {e}")
        await loading_msg.delete()
        await update.message.reply_text(
            "❌ Error fetching weather for this location.\n"
            "Please try again or use city name instead."
        )
        return ConversationHandler.END

# ---------------------------
# Harvest Advice
# ---------------------------
async def harvest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Provide harvesting advice based on weather forecast"""
    city = update.message.text.strip().title()
    
    if city == "🔙 Back to Menu":
        return await show_menu(update, context)

    url = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?q={city}&appid={WEATHER_API_KEY}&units=metric"
    )

    try:
        loading_msg = await update.message.reply_text(f"🌾 Analyzing weather for {city}...")
        
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("cod") != "200":
            await loading_msg.delete()
            await update.message.reply_text(
                f"❌ Weather data unavailable for {city}.\n"
                f"Please check the city name or try sharing your location."
            )
            return ConversationHandler.END

        # Analyze next 3 days (24 intervals of 3 hours)
        total_rain = 0
        rain_days = 0
        temps = []
        humidities = []

        for i, entry in enumerate(data["list"][:24]):  # 3 days
            rain = entry.get("rain", {}).get("3h", 0)
            total_rain += rain
            if rain > 0:
                rain_days += 1
            temps.append(entry["main"]["temp"])
            humidities.append(entry["main"]["humidity"])

        avg_temp = sum(temps) / len(temps)
        avg_humidity = sum(humidities) / len(humidities)
        
        await loading_msg.delete()

        # Generate advice based on conditions
        message = f"🌾 *Harvest Advice for {city}*\n\n"
        message += f"📊 *Weather Analysis (Next 3 days)*\n"
        message += f"• Expected Rain: {total_rain:.1f}mm\n"
        message += f"• Days with rain: {rain_days}/8 periods\n"
        message += f"• Avg Temperature: {avg_temp:.1f}°C\n"
        message += f"• Avg Humidity: {avg_humidity:.0f}%\n\n"

        # Determine harvest suitability
        if total_rain < 2:
            message += "✅ *OPTIMAL CONDITIONS*\n"
            message += "• Weather is stable and dry\n"
            message += "• Ideal for harvesting most crops\n"
            message += "• Best time: Next 2-3 days\n"
            message += "• Store in dry place after harvest\n"
        elif total_rain < 10:
            message += "⚠️ *CAUTION ADVISED*\n"
            message += "• Light rain expected\n"
            message += "• Harvest within next 24 hours if possible\n"
            message += "• Ensure proper drying after harvest\n"
            message += "• Consider covered storage\n"
        else:
            message += "❌ *NOT RECOMMENDED*\n"
            message += "• Significant rain expected\n"
            message += "• Delay harvesting for 4-5 days\n"
            message += "• Monitor field for waterlogging\n"
            message += "• Check crop for diseases\n"

        # Crop-specific advice
        message += "\n*Crop Recommendations:*\n"
        
        if avg_temp > 35:
            message += "• 🌡 Heat wave alert! Harvest early morning\n"
        elif avg_temp < 15:
            message += "• ❄ Cold conditions - protect sensitive crops\n"
        
        if avg_humidity > 80:
            message += "• 💧 High humidity - risk of fungal diseases\n"
            message += "• Ensure good air circulation for stored crops\n"
        
        if total_rain > 20:
            message += "• 🌧 Heavy rain expected - check drainage\n"
            message += "• Delay harvest for grains and pulses\n"
        else:
            message += "• 🌾 Good time for harvesting grains\n"
            message += "• Vegetables can be harvested as needed\n"

        await update.message.reply_text(message, parse_mode='Markdown')

        # Ask for next action
        keyboard = [["🌾 Another City"], ["📍 Share Location"], ["🔙 Back to Menu"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "What would you like to do next?",
            reply_markup=reply_markup
        )
        return MENU

    except Exception as e:
        logger.error(f"Error in harvest advice: {e}")
        await update.message.reply_text("❌ Error generating harvest advice.")
        return ConversationHandler.END

# ---------------------------
# Error Handler
# ---------------------------
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in the bot"""
    logger.error(f"Update {update} caused error {context.error}")
    
    try:
        if update and update.message:
            await update.message.reply_text(
                "❌ An error occurred. Please try again later or type /start"
            )
    except:
        pass

# ---------------------------
# Main Function
# ---------------------------
def main():
    """Main function to run the bot"""
    # Validate environment before starting
    if not validate_env():
        print("❌ Bot cannot start due to missing environment variables.")
        print("Please check your .env file and ensure all required keys are set.")
        return

    try:
        # Create application
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        # Add error handler
        app.add_error_handler(error_handler)

        # Create conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler)],
                MARKET_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, market_state)],
                MARKET: [MessageHandler(filters.TEXT & ~filters.COMMAND, market_price)],
                WEATHER: [MessageHandler(filters.TEXT & ~filters.COMMAND, weather)],
                LOCATION_WEATHER: [
                    MessageHandler(filters.LOCATION, weather_by_location),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, weather_by_location)
                ],
                HARVEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, harvest)],
            },
            fallbacks=[
                CommandHandler("cancel", cancel),
                MessageHandler(filters.Regex('^❌ Cancel$'), cancel),
                MessageHandler(filters.Regex('^🔙 Back to Menu$'), show_menu)
            ],
            name="krishi_bot_conversation",
            persistent=False
        )

        # Add handlers
        app.add_handler(conv_handler)
        
        # Add help command
        async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            help_text = (
                "🤖 *Smart Krishi AI Bot Help*\n\n"
                "*Commands:*\n"
                "/start - Start the bot\n"
                "/cancel - Cancel current operation\n"
                "/help - Show this help message\n\n"
                "*Features:*\n"
                "📈 *Market Prices* - Get crop prices by state (hybrid: local + API)\n"
                "🌤 *Weather* - Forecast by city name\n"
                "📍 *Share Location* - Weather at your location\n"
                "🌾 *Harvest Advice* - Best time to harvest based on weather\n\n"
                "*Data Sources:*\n"
                "• Market data: data.gov.in (AGMARKNET) + Local cache\n"
                "• Weather data: OpenWeatherMap\n\n"
                "*Tips:*\n"
                "• Local data loads instantly for common crops\n"
                "• Live API fetches real-time data when needed\n"
                "• You can save API results to local database"
            )
            await update.message.reply_text(help_text, parse_mode='Markdown')
        
        app.add_handler(CommandHandler("help", help_command))

        # Start the bot
        print("✅ Bot is running... Press Ctrl+C to stop.")
        print("📱 Test your bot on Telegram now!")
        app.run_polling()

    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"❌ Failed to start bot: {e}")

if __name__ == "__main__":
    main()