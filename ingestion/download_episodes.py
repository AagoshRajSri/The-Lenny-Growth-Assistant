import os
import json
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime

RSS_URL = "https://www.lennysnewsletter.com/feed"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")

def fetch_episodes():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    print(f"Fetching RSS feed from {RSS_URL}...")
    feed = feedparser.parse(RSS_URL)
    
    # Take the latest 25 episodes
    episodes = feed.entries[:25]
    print(f"Found {len(episodes)} episodes.")
    
    count = 0
    for entry in episodes:
        title = entry.get('title', 'Unknown Title')
        link = entry.get('link', '')
        published = entry.get('published', '')
        
        # Get content or description
        content_html = ''
        if 'content' in entry and len(entry.content) > 0:
            content_html = entry.content[0].value
        else:
            content_html = entry.get('summary', entry.get('description', ''))
            
        # Strip HTML
        soup = BeautifulSoup(content_html, "html.parser")
        text_content = soup.get_text(separator="\n", strip=True)
        
        # Parse date if possible
        try:
            pub_date = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %Z").isoformat()
        except ValueError:
            pub_date = published
            
        data = {
            "title": title,
            "url": link,
            "published_at": pub_date,
            "text": text_content
        }
        
        # Save to file
        safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip().replace(" ", "_").lower()
        if not safe_title:
            safe_title = f"episode_{count}"
            
        filename = os.path.join(OUTPUT_DIR, f"{safe_title[:50]}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        count += 1
        
    print(f"Successfully downloaded and saved {count} episodes to {OUTPUT_DIR}")

if __name__ == "__main__":
    fetch_episodes()
