# local_data_manager.py
import csv
import json
import os
import requests
from datetime import datetime
from pathlib import Path

class LocalMarketData:
    """Manage local market price data with API fallback"""
    
    def __init__(self, data_dir="market_data"):
        self.data_dir = data_dir
        self.data_file = None
        self.data = {}
        self.last_updated = None
        self.data_source = "sample"  # sample, local, or api
        
        # Create data directory if it doesn't exist
        Path(data_dir).mkdir(exist_ok=True)
        
        # Load existing data or create sample data
        self.load_or_create_data()
    
    def load_or_create_data(self):
        """Load existing data file or create sample data"""
        
        # Look for existing data files
        data_files = list(Path(self.data_dir).glob("market_data_*.json"))
        data_files.extend(Path(self.data_dir).glob("market_data_*.csv"))
        
        if data_files:
            # Use the most recent file
            self.data_file = max(data_files, key=os.path.getctime)
            self.load_data()
            self.data_source = "local"
            print(f"✅ Loaded local data from: {self.data_file}")
        else:
            # Create sample data
            self.create_sample_data()
            self.data_source = "sample"
            print("✅ Using sample data (no local file found)")
    
    def create_sample_data(self):
        """Create comprehensive sample data for demo"""
        self.data = {
            "Onion": {
                "Maharashtra": [
                    {"market": "Lasalgaon", "min_price": 1500, "max_price": 3500, "modal_price": 2500, "arrival_date": "2024-03-01"},
                    {"market": "Pune", "min_price": 1400, "max_price": 3300, "modal_price": 2400, "arrival_date": "2024-03-01"},
                    {"market": "Nashik", "min_price": 1550, "max_price": 3400, "modal_price": 2600, "arrival_date": "2024-03-01"},
                    {"market": "Nagpur", "min_price": 1450, "max_price": 3200, "modal_price": 2300, "arrival_date": "2024-03-01"}
                ],
                "Karnataka": [
                    {"market": "Bangalore", "min_price": 1600, "max_price": 3600, "modal_price": 2700, "arrival_date": "2024-03-01"},
                    {"market": "Mysore", "min_price": 1550, "max_price": 3400, "modal_price": 2600, "arrival_date": "2024-03-01"}
                ],
                "Punjab": [
                    {"market": "Ludhiana", "min_price": 1400, "max_price": 3200, "modal_price": 2300, "arrival_date": "2024-03-01"}
                ]
            },
            "Potato": {
                "Maharashtra": [
                    {"market": "Pune", "min_price": 800, "max_price": 1500, "modal_price": 1100, "arrival_date": "2024-03-01"},
                    {"market": "Nashik", "min_price": 750, "max_price": 1400, "modal_price": 1050, "arrival_date": "2024-03-01"}
                ],
                "Uttar Pradesh": [
                    {"market": "Agra", "min_price": 800, "max_price": 1500, "modal_price": 1100, "arrival_date": "2024-03-01"},
                    {"market": "Lucknow", "min_price": 750, "max_price": 1400, "modal_price": 1000, "arrival_date": "2024-03-01"},
                    {"market": "Kanpur", "min_price": 780, "max_price": 1450, "modal_price": 1080, "arrival_date": "2024-03-01"}
                ],
                "Punjab": [
                    {"market": "Jalandhar", "min_price": 700, "max_price": 1300, "modal_price": 950, "arrival_date": "2024-03-01"},
                    {"market": "Amritsar", "min_price": 720, "max_price": 1350, "modal_price": 980, "arrival_date": "2024-03-01"}
                ]
            },
            "Tomato": {
                "Maharashtra": [
                    {"market": "Nashik", "min_price": 1000, "max_price": 2500, "modal_price": 1700, "arrival_date": "2024-03-01"},
                    {"market": "Pune", "min_price": 1100, "max_price": 2400, "modal_price": 1600, "arrival_date": "2024-03-01"},
                    {"market": "Nagpur", "min_price": 1050, "max_price": 2300, "modal_price": 1650, "arrival_date": "2024-03-01"}
                ],
                "Karnataka": [
                    {"market": "Kolar", "min_price": 900, "max_price": 2200, "modal_price": 1500, "arrival_date": "2024-03-01"},
                    {"market": "Bangalore", "min_price": 950, "max_price": 2300, "modal_price": 1600, "arrival_date": "2024-03-01"}
                ],
                "Andhra Pradesh": [
                    {"market": "Chittoor", "min_price": 850, "max_price": 2100, "modal_price": 1400, "arrival_date": "2024-03-01"}
                ]
            },
            "Wheat": {
                "Punjab": [
                    {"market": "Ludhiana", "min_price": 1800, "max_price": 2200, "modal_price": 2000, "arrival_date": "2024-03-01"},
                    {"market": "Patiala", "min_price": 1750, "max_price": 2150, "modal_price": 1950, "arrival_date": "2024-03-01"}
                ],
                "Haryana": [
                    {"market": "Karnal", "min_price": 1780, "max_price": 2180, "modal_price": 1980, "arrival_date": "2024-03-01"},
                    {"market": "Hisar", "min_price": 1760, "max_price": 2160, "modal_price": 1960, "arrival_date": "2024-03-01"}
                ],
                "Uttar Pradesh": [
                    {"market": "Meerut", "min_price": 1750, "max_price": 2150, "modal_price": 1950, "arrival_date": "2024-03-01"}
                ]
            },
            "Rice": {
                "West Bengal": [
                    {"market": "Bardhaman", "min_price": 2000, "max_price": 2800, "modal_price": 2400, "arrival_date": "2024-03-01"},
                    {"market": "Hooghly", "min_price": 1950, "max_price": 2750, "modal_price": 2350, "arrival_date": "2024-03-01"}
                ],
                "Punjab": [
                    {"market": "Amritsar", "min_price": 2100, "max_price": 2900, "modal_price": 2500, "arrival_date": "2024-03-01"}
                ],
                "Andhra Pradesh": [
                    {"market": "West Godavari", "min_price": 2050, "max_price": 2850, "modal_price": 2450, "arrival_date": "2024-03-01"}
                ]
            },
            "Sugarcane": {
                "Uttar Pradesh": [
                    {"market": "Meerut", "min_price": 2800, "max_price": 3500, "modal_price": 3150, "arrival_date": "2024-03-01"},
                    {"market": "Muzaffarnagar", "min_price": 2750, "max_price": 3450, "modal_price": 3100, "arrival_date": "2024-03-01"}
                ],
                "Maharashtra": [
                    {"market": "Kolhapur", "min_price": 2900, "max_price": 3600, "modal_price": 3250, "arrival_date": "2024-03-01"},
                    {"market": "Sangli", "min_price": 2850, "max_price": 3550, "modal_price": 3200, "arrival_date": "2024-03-01"}
                ]
            }
        }
        self.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    def load_data(self):
        """Load data from file"""
        try:
            if self.data_file.suffix == '.json':
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            elif self.data_file.suffix == '.csv':
                self.load_csv_data()
            
            self.last_updated = datetime.fromtimestamp(os.path.getctime(self.data_file)).strftime("%Y-%m-%d %H:%M")
            
        except Exception as e:
            print(f"Error loading data: {e}")
            self.create_sample_data()
    
    def load_csv_data(self):
        """Load and convert CSV data"""
        self.data = {}
        with open(self.data_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                crop = row.get('commodity', '').title()
                state = row.get('state', '').title()
                
                if not crop or not state:
                    continue
                
                if crop not in self.data:
                    self.data[crop] = {}
                if state not in self.data[crop]:
                    self.data[crop][state] = []
                
                self.data[crop][state].append({
                    'market': row.get('market', 'Unknown'),
                    'min_price': row.get('min_price', row.get('minimum_price', 'N/A')),
                    'max_price': row.get('max_price', row.get('maximum_price', 'N/A')),
                    'modal_price': row.get('modal_price', row.get('modal_price', 'N/A')),
                    'arrival_date': row.get('arrival_date', row.get('date', 'N/A'))
                })
    
    def query(self, crop, state):
        """Query prices for crop and state"""
        crop = crop.title()
        state = state.title()
        
        if crop in self.data and state in self.data[crop]:
            return self.data[crop][state]
        return None
    
    def get_all_crops(self):
        """Get list of all available crops"""
        return list(self.data.keys())
    
    def get_all_states(self, crop):
        """Get all states for a crop"""
        if crop in self.data:
            return list(self.data[crop].keys())
        return []
    
    def save_to_file(self, filename=None):
        """Save current data to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.data_dir / f"market_data_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        
        self.data_file = filename
        self.data_source = "local"
        print(f"✅ Data saved to: {filename}")
        return filename

# Create global instance
market_data = LocalMarketData()