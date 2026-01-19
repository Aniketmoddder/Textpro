from fastapi import FastAPI
import cloudscraper
import json
import re
from bs4 import BeautifulSoup

app = FastAPI()

def generate_textpro(effect_url, user_text):
    # 1. Initialize scraper with a specific browser fingerprint
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    # 2. Add high-level headers that real browsers use
    scraper.headers.update({
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })

    try:
        # Step A: Get the page
        response = scraper.get(effect_url, timeout=10)
        
        # Check if we are stuck on a Cloudflare "Just a moment" page
        if "cf-challenge" in response.text or "ray-id" in response.text:
            return {"success": False, "error": "Vercel IP is blocked by Cloudflare. Try a different effect or wait."}

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Step B: Find the JSON data you discovered
        form_value_element = soup.find(id="form_value")
        
        if not form_value_element:
            # Fallback: Let's try to find it via Regex if the HTML is messy
            json_match = re.search(r'<div id="form_value" style="display:none">(.*?)</div>', response.text)
            if json_match:
                payload = json.loads(json_match.group(1))
            else:
                return {"success": False, "error": "Site detected a bot. form_value is missing."}
        else:
            payload = json.loads(form_value_element.text)

        # Step C: Set the text
        payload["text[]"] = [user_text]
        
        # Step D: Execute the creation
        post_url = "https://textpro.me/effect/create-image"
        # The Referer must be exact for the sign to work
        post_headers = {
            "Referer": effect_url,
            "Origin": "https://textpro.me",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        res = scraper.post(post_url, data=payload, headers=post_headers, timeout=15)
        
        if res.status_code == 200:
            return {"success": True, "image_url": f"{payload['build_server']}{res.json()['image']}"}
        
        return {"success": False, "error": f"POST failed with status {res.status_code}"}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/generate")
def api_endpoint(url: str, text: str):
    return generate_textpro(url, text)
