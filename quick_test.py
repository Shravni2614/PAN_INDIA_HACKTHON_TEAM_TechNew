# quick_test.py
import requests
from dotenv import load_dotenv
import os

load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
DATA_GOV_API_KEY = os.getenv("DATA_GOV_API_KEY")

def test_all_features():
    print("🌾 Testing All Bot Features...\n")
    
    # 1. Test Weather with different cities
    print("1️⃣ Testing Weather API:")
    cities = ["Mumbai", "Pune", "Nagpur", "Delhi"]
    for city in cities:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            print(f"   ✅ {city}: {data['main']['temp']}°C, {data['weather'][0]['description']}")
        else:
            print(f"   ❌ {city}: Failed")
    
    # 2. Test Market Prices with different crops
    print("\n2️⃣ Testing Market Prices API:")
    crops = ["Onion", "Potato", "Tomato", "Wheat", "Rice"]
    states = ["Maharashtra", "Punjab", "Uttar Pradesh"]
    
    for crop in crops:
        for state in states[:1]:  # Test only first state for brevity
            url = (
                "https://api.data.gov.in/resource/"
                "9ef84268-d588-465a-a308-a864a43d0070"
                f"?api-key={DATA_GOV_API_KEY}"
                "&format=json"
                f"&filters[commodity]={crop}"
                f"&filters[state]={state}"
                "&limit=1"
            )
            r = requests.get(url)
            if r.status_code == 200:
                data = r.json()
                if data.get("records"):
                    print(f"   ✅ {crop} in {state}: Data found")
                else:
                    print(f"   ⚠️ {crop} in {state}: No records (API working)")
            else:
                print(f"   ❌ {crop} in {state}: API error")
    
    # 3. Test Location/Geocoding
    print("\n3️⃣ Testing Geocoding API:")
    locations = [(19.0760, 72.8777, "Mumbai"), 
                 (18.5204, 73.8567, "Pune"),
                 (21.1458, 79.0882, "Nagpur")]
    
    for lat, lon, expected in locations:
        url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={WEATHER_API_KEY}"
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            if data:
                print(f"   ✅ Coordinates ({lat}, {lon}) → {data[0].get('name')}")
            else:
                print(f"   ⚠️ No location found")
        else:
            print(f"   ❌ Geocoding failed")
    
    # 4. Test Forecast API
    print("\n4️⃣ Testing 5-day Forecast:")
    url = f"https://api.openweathermap.org/data/2.5/forecast?q=Mumbai&appid={WEATHER_API_KEY}&units=metric"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        print(f"   ✅ Got {len(data.get('list', []))} forecast periods")
        
        # Show next 3 days
        daily_temps = {}
        for item in data['list'][:8]:  # First 24 hours
            date = item['dt_txt'].split()[0]
            if date not in daily_temps:
                daily_temps[date] = []
            daily_temps[date].append(item['main']['temp'])
        
        for date, temps in list(daily_temps.items())[:3]:
            avg_temp = sum(temps) / len(temps)
            print(f"      {date}: Avg {avg_temp:.1f}°C")
    else:
        print(f"   ❌ Forecast failed")

if __name__ == "__main__":
    test_all_features()