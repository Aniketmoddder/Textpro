from fastapi import FastAPI
from curl_cffi import requests
from bs4 import BeautifulSoup
import json
import re

app = FastAPI()

def solve_textpro(url, text):
    # 'impersonate' makes the TLS handshake look like a real browser
    session = requests.Session(impersonate="chrome120")
    
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://textpro.me/",
    }

    try:
        # Step 1: Get the page
        response = session.get(url, headers=headers, timeout=15)
        
        if "form_value" not in response.text:
            # If still blocked, we check if it's a Cloudflare challenge
            if "cf-challenge" in response.text or "Just a moment" in response.text:
                return {"success": False, "error": "TLS Bypassed but IP still flagged. Cloudflare challenge active."}
            return {"success": False, "error": "Could not find form data. Site layout might have changed."}

        soup = BeautifulSoup(response.text, 'html.parser')
        form_data = json.loads(soup.find(id="form_value").text)
        
        # Step 2: Prepare the payload
        form_data["text[]"] = [text]
        
        # Step 3: Send POST
        post_headers = headers.copy()
        post_headers.update({
            "Origin": "https://textpro.me",
            "Referer": url,
            "X-Requested-With": "XMLHttpRequest",
        })

        res = session.post(
            "https://textpro.me/effect/create-image",
            data=form_data,
            headers=post_headers,
            timeout=20
        )
        
        if res.status_code == 200:
            result = res.json()
            if result.get("success"):
                return {"success": True, "image_url": f"{form_data['build_server']}{result['image']}"}
            return {"success": False, "message": result.get("message")}
            
        return {"success": False, "error": f"POST failed: {res.status_code}"}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/generate")
def api(url: str, text: str):
    return solve_textpro(url, text)
