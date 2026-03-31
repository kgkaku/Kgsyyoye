import requests
import json
import time
from datetime import datetime

# ============ কনফিগারেশন ============
# Local Storage থেকে পাওয়া JWT টোকেন
JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6Ijg0..."  # আপনার টোকেন

HEADERS = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Origin": "https://iscreen.com.bd",
    "Referer": "https://iscreen.com.bd/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
}

# ============ সেশন তৈরি ============
def create_session():
    """নতুন সেশন তৈরি করে, স্বয়ংক্রিয়ভাবে nimblesessionid ম্যানেজ করে"""
    session = requests.Session()
    session.headers.update(HEADERS)
    
    # প্রথমে হোমপেজ লোড করে কুকি সংগ্রহ
    print("🍪 Getting session cookies...")
    homepage_response = session.get("https://iscreen.com.bd/")
    
    if homepage_response.status_code == 200:
        cookies = session.cookies.get_dict()
        print(f"   Cookies: {cookies}")
        if 'nimblesessionid' in cookies:
            print(f"   ✅ nimblesessionid: {cookies['nimblesessionid'][:20]}...")
    else:
        print(f"   ⚠️ Homepage returned {homepage_response.status_code}")
    
    return session

# ============ API ফাংশন ============
def fetch_live_channels(session):
    """API থেকে লাইভ চ্যানেল সংগ্রহ করে"""
    all_channels = []
    page = 1
    
    while True:
        print(f"\n📡 Fetching page {page}...")
        
        try:
            response = session.get(
                f"https://api.rockstreamer.com/api/category?page={page}&type=all"
            )
            
            if response.status_code == 401:
                print("❌ Token expired! Need new token.")
                return []
            
            response.raise_for_status()
            data = response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            break
        
        items = data.get('data', [])
        if not items:
            break
        
        # লাইভ চ্যানেল ফিল্টার
        live_items = [item for item in items if item.get('type') == 'live']
        all_channels.extend(live_items)
        print(f"   Found {len(live_items)} live channels (total: {len(all_channels)})")
        
        # পেজিনেশন চেক
        if not data.get('next_page_url'):
            break
        page += 1
    
    return all_channels

def generate_m3u(channels):
    """Extvlcopt ফরম্যাটে M3U ফাইল তৈরি"""
    m3u = "#EXTM3U\n"
    m3u += "#EXTVLCOPT:http-referer=https://iscreen.com.bd/\n"
    m3u += "#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36\n\n"
    
    for ch in channels:
        channel_id = ch.get('id')
        title = ch.get('title', 'Unknown')
        logo = ch.get('image', '')
        
        video_url = f"https://s3.brilliant.com.bd/videos/{channel_id}/master.m3u8"
        
        m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="Live TV",{title}\n'
        m3u += f"{video_url}\n\n"
    
    return m3u

def main():
    print("🚀 Starting iScreen scraper...")
    print("=" * 50)
    
    # সেশন তৈরি (স্বয়ংক্রিয়ভাবে nimblesessionid নেয়)
    session = create_session()
    
    # চ্যানেল ফেচ
    channels = fetch_live_channels(session)
    
    if channels:
        # JSON সেভ
        with open('iscreen.json', 'w', encoding='utf-8') as f:
            json.dump(channels, f, indent=2, ensure_ascii=False)
        
        # M3U সেভ
        with open('iscreen.m3u', 'w', encoding='utf-8') as f:
            f.write(generate_m3u(channels))
        
        print("\n" + "=" * 50)
        print(f"✅ Success! Saved {len(channels)} live channels")
        print(f"📅 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("📁 Files: iscreen.json, iscreen.m3u")
    else:
        print("\n⚠️ No live channels found!")

if __name__ == "__main__":
    main()
