from fastapi import FastAPI, Query
import requests
import re
from bs4 import BeautifulSoup

app = FastAPI()

class TextProAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        })

    def generate(self, effect_url: str, text: str):
        # 1. Scrape tokens
        response = self.session.get(effect_url)
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        
        try:
            token = soup.find("input", {"id": "token"})["value"]
            server = soup.find("input", {"id": "build_server"})["value"]
            server_id = soup.find("input", {"id": "build_server_id"})["value"]
            
            # Find the sign value in the raw HTML
            sign_match = re.search(r'name="sign"\s+value="([^"]+)"', html)
            if not sign_match:
                sign_match = re.search(r'sign"\s*:\s*"([^"]+)"', html) or re.search(r'sign\s*=\s*"([^"]+)"', html)
            
            if not sign_match:
                return {"error": "Could not find security sign"}

            sign = sign_match.group(1)
            effect_id = effect_url.split("-")[-1].replace(".html", "")

            # 2. Post Data
            payload = {
                "id": effect_id,
                "text[]": [text],
                "grecaptcharesponse": "", 
                "token": token,
                "build_server": server,
                "build_server_id": server_id,
                "sign": sign
            }

            headers = {"Referer": effect_url, "X-Requested-With": "XMLHttpRequest"}
            res = self.session.post("https://textpro.me/effect/create-image", data=payload, headers=headers)
            
            if res.status_code == 200:
                result = res.json()
                if result.get("success"):
                    return {"success": True, "image_url": f"https://textpro.me{result['image']}"}
                return {"success": False, "message": result.get("message")}
            
            return {"success": False, "message": f"HTTP Error {res.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# --- API Endpoints ---

@app.get("/")
def home():
    return {"status": "TextPro API is running"}

@app.get("/generate")
def create_effect(url: str, text: str):
    api = TextProAPI()
    return api.generate(url, text)
