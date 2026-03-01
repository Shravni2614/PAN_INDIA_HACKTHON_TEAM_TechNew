# admin.py
import os
import json
from local_data_manager import market_data
from download_market_data import DataGovDownloader
from dotenv import load_dotenv

load_dotenv()

def show_menu():
    """Show admin menu"""
    print("\n" + "="*50)
    print("🌾 LOCAL MARKET DATA ADMIN")
    print("="*50)
    print(f"Data source: {market_data.data_source}")
    print(f"Last updated: {market_data.last_updated}")
    print(f"Total crops: {len(market_data.get_all_crops())}")
    print("\nOptions:")
    print("1. View all crops")
    print("2. View crop details")
    print("3. Add sample data")
    print("4. Download from data.gov.in")
    print("5. Save current data")
    print("6. Export to CSV")
    print("7. Exit")
    return input("\nEnter choice: ").strip()

def view_crop_details():
    """View details for a specific crop"""
    crops = market_data.get_all_crops()
    print(f"\nAvailable crops: {', '.join(crops)}")
    
    crop = input("Enter crop name: ").strip().title()
    if crop in market_data.data:
        states = market_data.get_all_states(crop)
        print(f"\n📊 {crop}")
        print(f"States: {', '.join(states)}")
        
        for state in states:
            records = market_data.query(crop, state)
            print(f"\n  {state}: {len(records)} markets")
            for r in records[:3]:
                print(f"    - {r['market']}: ₹{r['modal_price']}")
    else:
        print("Crop not found")

def export_to_csv():
    """Export data to CSV"""
    import csv
    from datetime import datetime
    
    filename = f"market_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Crop', 'State', 'Market', 'Min Price', 'Max Price', 'Modal Price', 'Date'])
        
        for crop, states in market_data.data.items():
            for state, records in states.items():
                for record in records:
                    writer.writerow([
                        crop, state,
                        record.get('market', ''),
                        record.get('min_price', ''),
                        record.get('max_price', ''),
                        record.get('modal_price', ''),
                        record.get('arrival_date', '')
                    ])
    
    print(f"✅ Exported to {filename}")

def main():
    while True:
        choice = show_menu()
        
        if choice == '1':
            crops = market_data.get_all_crops()
            print(f"\n📋 Crops ({len(crops)}):")
            for i, crop in enumerate(crops, 1):
                states = len(market_data.get_all_states(crop))
                print(f"  {i}. {crop} ({states} states)")
        
        elif choice == '2':
            view_crop_details()
        
        elif choice == '3':
            market_data.create_sample_data()
            print("✅ Sample data added")
        
        elif choice == '4':
            downloader = DataGovDownloader()
            downloader.download_known_agricultural_datasets()
        
        elif choice == '5':
            filename = market_data.save_to_file()
            print(f"✅ Data saved to {filename}")
        
        elif choice == '6':
            export_to_csv()
        
        elif choice == '7':
            break
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()