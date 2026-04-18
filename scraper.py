import requests
import json
import re
from config import BOOKLET_URL, PANEL_BASE_URL
from database import update_latest_booklet, get_latest_booklet

def scrape_latest_booklet():
    try:
        response = requests.get(BOOKLET_URL)
        if response.status_code != 200:
            print(f"Failed to fetch {BOOKLET_URL}: {response.status_code}")
            return None
        
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json"[^>]*>(.*?)</script>', response.text, re.DOTALL)
        if not match:
            print("Could not find NEXT_DATA in HTML")
            return None
        
        data = json.loads(match.group(1))
        
        booklets_list = data.get('props', {}).get('pageProps', {}).get('data', [])
        
        if not booklets_list:
            booklets_list = data.get('props', {}).get('pageProps', {}).get('booklets', [])
            
        if not booklets_list:
            print("No booklets found in JSON data")
            return None
        
        latest_announcement = booklets_list[0]
        book_info = latest_announcement.get('book', {})
        book_languages = book_info.get('book_languages', [])
        
        title = book_info.get('name', 'Weekly Booklet')
        published_on = latest_announcement.get('announcement_date', '')
        
        hindi_url = None
        urdu_url = None
        
        for lang_info in book_languages:
            lang_id = lang_info.get('language_id')
            file_path = lang_info.get('file_path', '')
            
            if file_path:
                full_url = PANEL_BASE_URL + file_path
                if lang_id == 4:
                    hindi_url = full_url
                elif lang_id == 2:
                    urdu_url = full_url
        
        if hindi_url or urdu_url:
            print(f"Found latest booklet: {title} (Published: {published_on})")
            update_latest_booklet(title, hindi_url, urdu_url, published_on)
            return {
                'title': title,
                'hindi_url': hindi_url,
                'urdu_url': urdu_url,
                'published_on': published_on
            }
        
        return None
        
    except Exception as e:
        print(f"Error scraping booklet: {e}")
        return None

if __name__ == "__main__":
    from database import init_db
    init_db()
    result = scrape_latest_booklet()
    print(f"Result: {result}")
