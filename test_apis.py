# test_apis.py
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
DATA_GOV_API_KEY = os.getenv("DATA_GOV_API_KEY")

def test_telegram_bot_token():
    """Test Telegram Bot Token"""
    print("\n🔍 Testing Telegram Bot Token...")
    
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not found in .env file")
        return False
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("ok"):
            bot_info = data["result"]
            print(f"✅ Telegram Bot is working!")
            print(f"   Bot Name: {bot_info.get('first_name')}")
            print(f"   Username: @{bot_info.get('username')}")
            return True
        else:
            print(f"❌ Invalid Telegram Bot Token")
            print(f"   Error: {data.get('description')}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to Telegram API: {e}")
        return False

def test_openweather_api():
    """Test OpenWeatherMap API"""
    print("\n🔍 Testing OpenWeatherMap API...")
    
    if not WEATHER_API_KEY:
        print("❌ WEATHER_API_KEY not found in .env file")
        return False
    
    # Test with a known city
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Mumbai&appid={WEATHER_API_KEY}&units=metric"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if response.status_code == 200:
            print(f"✅ OpenWeatherMap API is working!")
            print(f"   City: Mumbai")
            print(f"   Temperature: {data['main']['temp']}°C")
            print(f"   Weather: {data['weather'][0]['description']}")
            return True
        else:
            print(f"❌ OpenWeatherMap API Error")
            print(f"   Code: {data.get('cod')}")
            print(f"   Message: {data.get('message')}")
            
            # Specific error messages
            if data.get('cod') == 401:
                print("   → Invalid API Key")
            elif data.get('cod') == 429:
                print("   → Too many requests (rate limited)")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to OpenWeatherMap API: {e}")
        return False

def test_data_gov_api():
    """Test Data.gov.in API"""
    print("\n🔍 Testing Data.gov.in API...")
    
    if not DATA_GOV_API_KEY:
        print("❌ DATA_GOV_API_KEY not found in .env file")
        return False
    
    # Test with a common crop
    url = (
        "https://api.data.gov.in/resource/"
        "9ef84268-d588-465a-a308-a864a43d0070"
        f"?api-key={DATA_GOV_API_KEY}"
        "&format=json"
        "&filters[commodity]=Onion"
        "&filters[state]=Maharashtra"
        "&limit=1"
    )
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if response.status_code == 200:
            if "records" in data and data["records"]:
                print(f"✅ Data.gov.in API is working!")
                record = data["records"][0]
                print(f"   Found data for: Onion in Maharashtra")
                print(f"   Market: {record.get('market', 'N/A')}")
                print(f"   Price: ₹{record.get('modal_price', 'N/A')}")
                return True
            else:
                print(f"✅ API connected but no records found")
                print(f"   This might be normal if no data for the test query")
                return True
        else:
            print(f"❌ Data.gov.in API Error")
            print(f"   Status Code: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to Data.gov.in API: {e}")
        return False

def test_openweather_forecast():
    """Test OpenWeatherMap 5-day forecast endpoint"""
    print("\n🔍 Testing OpenWeatherMap Forecast API...")
    
    if not WEATHER_API_KEY:
        return False
    
    url = f"https://api.openweathermap.org/data/2.5/forecast?q=Mumbai&appid={WEATHER_API_KEY}&units=metric"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if response.status_code == 200:
            print(f"✅ Forecast API is working!")
            print(f"   Number of forecasts: {len(data.get('list', []))}")
            return True
        else:
            print(f"❌ Forecast API Error: {data.get('message')}")
            return False
    except:
        return False

def test_geocoding_api():
    """Test OpenWeatherMap Geocoding API"""
    print("\n🔍 Testing Geocoding API (for location weather)...")
    
    if not WEATHER_API_KEY:
        return False
    
    # Test reverse geocoding with coordinates
    url = f"http://api.openweathermap.org/geo/1.0/reverse?lat=19.0760&lon=72.8777&limit=1&appid={WEATHER_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if response.status_code == 200 and data:
            print(f"✅ Geocoding API is working!")
            print(f"   Location: {data[0].get('name')}, {data[0].get('country')}")
            return True
        else:
            print(f"❌ Geocoding API Error")
            return False
    except:
        print(f"❌ Cannot connect to Geocoding API")
        return False

def check_rate_limits():
    """Check if APIs are rate limited"""
    print("\n🔍 Checking Rate Limits...")
    
    # Test weather API with multiple quick requests
    print("   Testing rate limits (3 quick requests)...")
    
    success_count = 0
    for i in range(3):
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q=Mumbai&appid={WEATHER_API_KEY}&units=metric"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                print(f"   ⚠️ Request {i+1}: Rate limited!")
        except:
            pass
    
    if success_count == 3:
        print("   ✅ No rate limiting detected")
    else:
        print(f"   ⚠️ Only {success_count}/3 requests succeeded")

def main():
    """Run all API tests"""
    print("=" * 50)
    print("🌾 SMART KRISHI AI - API TESTER")
    print("=" * 50)
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("\n❌ .env file not found!")
        print("   Please create a .env file with your API keys")
        return
    
    # Run tests
    results = []
    
    print("\n📋 Testing APIs...")
    results.append(("Telegram Bot", test_telegram_bot_token()))
    results.append(("OpenWeatherMap Current", test_openweather_api()))
    results.append(("OpenWeatherMap Forecast", test_openweather_forecast()))
    results.append(("Geocoding API", test_geocoding_api()))
    results.append(("Data.gov.in", test_data_gov_api()))
    
    # Check rate limits only if weather API works
    if WEATHER_API_KEY:
        check_rate_limits()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ ALL TESTS PASSED! Your bot is ready to run.")
    else:
        print("⚠️ SOME TESTS FAILED. Check the errors above.")
        print("\nCommon fixes:")
        print("1. Verify API keys in .env file")
        print("2. Check internet connection")
        print("3. For Data.gov.in: Ensure API key has access to this dataset")
        print("4. For OpenWeatherMap: Free tier allows 60 calls/minute")
    print("=" * 50)

if __name__ == "__main__":
    main()