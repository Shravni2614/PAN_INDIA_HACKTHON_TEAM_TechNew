# location_handler.py
import reverse_geocoder as rg
import pycountry
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import timezonefinder
import pytz
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class LocationService:
    """Handle all location-based services"""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="smart_krishi_bot")
        self.tf = timezonefinder.TimezoneFinder()
        
    def get_location_from_coords(self, lat, lon):
        """
        Get detailed location information from coordinates
        Returns: dict with country, state, district, city, village
        """
        try:
            # Use reverse geocoding
            result = rg.search((lat, lon))[0]
            
            # Get admin boundaries
            location_data = {
                'latitude': lat,
                'longitude': lon,
                'country_code': result.get('cc', 'IN'),
                'country': self._get_country_name(result.get('cc', 'IN')),
                'state': result.get('admin1', ''),
                'district': result.get('admin2', ''),
                'city': result.get('name', ''),
                'village': result.get('name', '') if 'village' in result.get('admin2', '').lower() else '',
                'pin_code': self._get_pincode(lat, lon)
            }
            
            return location_data
            
        except Exception as e:
            logger.error(f"Error in reverse geocoding: {e}")
            return self.get_location_fallback(lat, lon)
    
    def _get_country_name(self, country_code):
        """Convert country code to full name"""
        try:
            country = pycountry.countries.get(alpha_2=country_code)
            return country.name if country else "India"
        except:
            return "India"
    
    def _get_pincode(self, lat, lon):
        """Get pincode for coordinates (approximate)"""
        try:
            location = self.geolocator.reverse(f"{lat}, {lon}", exactly_one=True)
            if location and location.raw.get('address'):
                return location.raw['address'].get('postcode', 'N/A')
        except:
            pass
        return "N/A"
    
    def get_location_fallback(self, lat, lon):
        """Fallback method if primary geocoding fails"""
        return {
            'latitude': lat,
            'longitude': lon,
            'country': 'India',
            'state': 'Unknown',
            'district': 'Unknown',
            'city': 'Unknown',
            'village': 'Unknown',
            'pin_code': 'N/A',
            'country_code': 'IN'
        }
    
    def get_timezone(self, lat, lon):
        """Get timezone for coordinates"""
        try:
            timezone_str = self.tf.timezone_at(lat=lat, lng=lon)
            if timezone_str:
                return pytz.timezone(timezone_str)
        except:
            pass
        return pytz.UTC
    
    def get_local_time(self, lat, lon):
        """Get local time at coordinates"""
        tz = self.get_timezone(lat, lon)
        return datetime.now(tz)
    
    def get_nearest_mandi(self, lat, lon, mandi_list=None):
        """Find nearest agricultural market (mandi)"""
        if not mandi_list:
            # Sample mandi coordinates (you can expand this)
            mandi_list = [
                {"name": "Lasalgaon APMC", "lat": 20.1427, "lon": 74.2254, "state": "Maharashtra"},
                {"name": "Pune APMC", "lat": 18.5204, "lon": 73.8567, "state": "Maharashtra"},
                {"name": "Nashik APMC", "lat": 19.9975, "lon": 73.7898, "state": "Maharashtra"},
                {"name": "Nagpur APMC", "lat": 21.1458, "lon": 79.0882, "state": "Maharashtra"},
                {"name": "Agra Mandi", "lat": 27.1767, "lon": 78.0081, "state": "Uttar Pradesh"},
                {"name": "Ludhiana Mandi", "lat": 30.9010, "lon": 75.8573, "state": "Punjab"},
                {"name": "Bangalore APMC", "lat": 12.9716, "lon": 77.5946, "state": "Karnataka"},
            ]
        
        user_location = (lat, lon)
        nearest = None
        min_distance = float('inf')
        
        for mandi in mandi_list:
            mandi_location = (mandi["lat"], mandi["lon"])
            distance = geodesic(user_location, mandi_location).kilometers
            
            if distance < min_distance:
                min_distance = distance
                nearest = mandi.copy()
                nearest["distance_km"] = round(distance, 2)
        
        return nearest
    
    def get_agricultural_zone(self, lat, lon):
        """Determine agricultural/horticultural zone"""
        # Simplified zone mapping (you can expand this)
        zones = {
            "North": ["Punjab", "Haryana", "Uttar Pradesh", "Himachal Pradesh"],
            "South": ["Karnataka", "Tamil Nadu", "Kerala", "Andhra Pradesh"],
            "East": ["West Bengal", "Bihar", "Odisha", "Assam"],
            "West": ["Maharashtra", "Gujarat", "Rajasthan", "Madhya Pradesh"],
            "Central": ["Madhya Pradesh", "Chhattisgarh"]
        }
        
        location = self.get_location_from_coords(lat, lon)
        state = location.get('state', '')
        
        for zone, states in zones.items():
            if any(s in state for s in states):
                return zone
        
        return "Unknown"

# Create global instance
location_service = LocationService()