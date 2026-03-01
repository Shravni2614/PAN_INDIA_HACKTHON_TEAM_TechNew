# download_market_data.py
import requests
import json
import csv
import os
from datetime import datetime
from pathlib import Path

class DataGovDownloader:
    """Download market data from data.gov.in"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("DATA_GOV_API_KEY")
        self.data_dir = Path("market_data")
        self.data_dir.mkdir(exist_ok=True)
    
    def search_datasets(self, query="agricultural prices mandi"):
        """Search for datasets on data.gov.in"""
        
        # Use catalog API to search
        url = "https://data.gov.in/api/3/action/package_search"
        params = {
            'q': query,
            'rows': 20
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            if data.get('success'):
                print(f"\n📊 Found {data['result']['count']} datasets:")
                for i, result in enumerate(data['result']['results'][:10], 1):
                    print(f"\n{i}. {result.get('title')}")
                    print(f"   Organization: {result.get('organization', {}).get('title', 'N/A')}")
                    
                    # Show resources
                    for resource in result.get('resources', [])[:3]:
                        print(f"   - {resource.get('format')}: {resource.get('url')}")
                
                return data['result']['results']
            else:
                print("❌ Search failed")
                return []
                
        except Exception as e:
            print(f"❌ Error searching: {e}")
            return []
    
    def download_dataset(self, resource_id, format='json'):
        """Download specific dataset by resource ID"""
        
        # Try different download URLs
        urls = [
            f"https://data.gov.in/node/{resource_id}/datastore/export/{format}",
            f"https://api.data.gov.in/resource/{resource_id}?api-key={self.api_key}&format={format}&limit=10000"
        ]
        
        for url in urls:
            try:
                print(f"   Trying: {url}")
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = self.data_dir / f"dataset_{resource_id[:8]}_{timestamp}.{format}"
                    
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"   ✅ Downloaded: {filename}")
                    return filename
                    
            except Exception as e:
                print(f"   ❌ Failed: {e}")
        
        return None
    
    def download_known_agricultural_datasets(self):
        """Download known agricultural datasets"""
        
        # These are example resource IDs - you'll need to find actual ones
        known_resources = [
            "9ef84268-d588-465a-a308-a864a43d0070",  # Your current one
            # Add more after searching
        ]
        
        downloaded = []
        for res_id in known_resources:
            print(f"\n🔍 Trying resource: {res_id}")
            filename = self.download_dataset(res_id, 'json')
            if filename:
                downloaded.append(filename)
            filename = self.download_dataset(res_id, 'csv')
            if filename:
                downloaded.append(filename)
        
        return downloaded

def main():
    """Main download function"""
    print("=" * 60)
    print("🌾 DATA.GOV.IN MARKET DATA DOWNLOADER")
    print("=" * 60)
    
    # Load API key from .env
    from dotenv import load_dotenv
    load_dotenv()
    
    downloader = DataGovDownloader()
    
    while True:
        print("\nOptions:")
        print("1. Search for agricultural datasets")
        print("2. Download by resource ID")
        print("3. Download known datasets")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            query = input("Enter search query (default: agricultural prices mandi): ").strip()
            if not query:
                query = "agricultural prices mandi"
            downloader.search_datasets(query)
            
        elif choice == '2':
            res_id = input("Enter resource ID: ").strip()
            fmt = input("Format (json/csv) [json]: ").strip() or 'json'
            downloader.download_dataset(res_id, fmt)
            
        elif choice == '3':
            downloaded = downloader.download_known_agricultural_datasets()
            if downloaded:
                print(f"\n✅ Downloaded {len(downloaded)} files:")
                for f in downloaded:
                    print(f"   - {f}")
            else:
                print("\n❌ No datasets downloaded")
                
        elif choice == '4':
            break
    
    print("\n✅ Done!")

if __name__ == "__main__":
    main()