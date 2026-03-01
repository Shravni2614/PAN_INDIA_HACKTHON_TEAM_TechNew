# test_location.py
from location_handler import location_service

def test_location():
    """Test location features with sample coordinates"""
    
    # Test with Mumbai coordinates
    print("Testing with Mumbai coordinates...")
    mumbai = location_service.get_location_from_coords(19.0760, 72.8777)
    print(f"Location: {mumbai['city']}, {mumbai['state']}, {mumbai['country']}")
    print(f"PIN: {mumbai['pin_code']}")
    
    # Test nearest mandi
    nearest = location_service.get_nearest_mandi(19.0760, 72.8777)
    print(f"Nearest Mandi: {nearest['name']} ({nearest['distance_km']} km)")
    
    # Test agricultural zone
    zone = location_service.get_agricultural_zone(19.0760, 72.8777)
    print(f"Agricultural Zone: {zone}")
    
    # Test local time
    local_time = location_service.get_local_time(19.0760, 72.8777)
    print(f"Local Time: {local_time.strftime('%I:%M %p')}")

if __name__ == "__main__":
    test_location()