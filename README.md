# PAN India Hackathon Project - TechNew

## 🌾 Project Overview
TechNew is a smart solution developed for the PAN India Hackathon.  
It helps farmers across India to get **real-time crop price updates**, **weather alerts**, and **storage suggestions** to make informed decisions.

💬 To try the Telegram bot, type **[@AgriAssistAI_bot]

## 🖼 Screenshots
Here’s how the app looks:  
![1](https://github.com/user-attachments/assets/5b5de0ab-8811-49f6-baa1-d20b4fe095b9)
![2](https://github.com/user-attachments/assets/3b98c98c-70e9-468f-ba43-e09b0956426b)
![3](https://github.com/user-attachments/assets/09781cd3-1704-4df6-9df9-7598753e52ab)
![4](https://github.com/user-attachments/assets/22116612-216f-48e0-a38f-2304ab431314)
![5](https://github.com/user-attachments/assets/9d5829ed-9bd1-4303-8083-10a0555f4aa4)
![6](https://github.com/user-attachments/assets/1155d5f2-6b70-4622-a889-983a19646ccc)

## 🛠 Features & Advantages
- **No App Download Needed:** Farmers don’t need to download any app or create accounts. Just open Telegram and type [@AgriAssistAI_bot](https://t.me/AgriAssistAI_bot).  
- **All-in-One Solution:** Crop prices, weather alerts, and storage suggestions are available in a single bot. No need to check multiple apps.  
- **User-Friendly Inline Buttons:** Makes navigation easy even for farmers who are not tech-savvy.  
- **Real-Time Updates:** Market prices and weather alerts are updated in real-time.  
- **Minimal Data Usage:** Works smoothly even on low-speed internet.   
- **Secure & Private:** No personal information or sign-up required. Farmers can use it safely.  
- **Portable:** Accessible from any smartphone with Telegram installed.  

## ⚙️ Technologies Used
- **Python** – For bot logic and data handling  
- **Python-Telegram-Bot** – To create the Telegram bot and inline buttons  
- **Requests / APIs** – To fetch real-time crop prices, weather info, and storage tips  
- **JSON / CSV** – For structured data storage  
- **GitHub** – Project hosting and version control  

---

## 🔄 How It Works
1. **User Interaction:** Farmer interacts with the bot via Telegram commands or inline buttons.  
2. **Bot Scripts:**  
   - `bot.py` – Main bot script  
   - `admin.py` – Admin features  
   - `quick_test.py` & `test_*.py` – Testing scripts  
3. **Data Handling:**  
   - `download_market_data.py` – Fetches latest market data from APIs  
   - `local_data_manager.py` – Manages local CSV data  
   - `location_handler.py` – Handles farmer location for nearest markets  
4. **Response:** Bot sends formatted updates on crop prices, weather, and storage suggestions.  

> Example: Farmer clicks “Crop Prices → Onion” → Bot fetches latest data from CSV/API → Bot shows nearest market prices.

---

## 💻 Installation / Run Locally

1. **Clone the repository**
```bash
git clone https://github.com/Shravni2614/PAN_INDIA_HACKTHON_TEAM_TechNew.git
cd PAN_INDIA_HACKTHON_TEAM_TechNew
```
2. **Install dependencies**
```bash
pip install -r requirements.txt
```
4. **Run the project**
```bash
python main.py
```

---

## 📁Folder & File Structure
```bash
PAN_INDIA_HACKTHON_TEAM_TECHNEW/
│
├─ bot.py                 # Main Telegram bot script
├─ admin.py               # Admin scripts
├─ download_market_data.py # Fetch market data from API
├─ local_data_manager.py   # Manage local CSV data
├─ location_handler.py     # Handle user location
├─ market_data_export_20260301_120212.csv # Sample market data
├─ quick_test.py           # Quick test script
├─ test_*.py               # Testing scripts
├─ requirements.txt        # Python dependencies
├─ .env                    # Environment variables (API keys)
├─ .gitignore
├─ __pycache__/            # Python cache files
└─ README.md               # This file
```
