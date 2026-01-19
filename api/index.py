from fastapi import FastAPI
import httpx
import json
import re
from bs4 import BeautifulSoup

app = FastAPI()

@app.get("/generate")
async def generate_textpro(url: str, text: str):
    # Using HTTP/2 is key to bypassing Cloudflare on Vercel
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    async with httpx.AsyncClient(http2=True, limits=limits, follow_redirects=True) as client:
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "max-age=0",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
        }

        try:
            # 1. GET request to fetch the page and tokens
            resp = await client.get(url, headers=headers)
            
            # If Cloudflare blocks us, we will see it in the title
            if "Just a moment" in resp.text:
                 # Try a fallback: extract tokens using raw regex if BeautifulSoup fails
                 return {"success": False, "error": "Cloudflare challenge active. Vercel is still being flagged."}

            soup = BeautifulSoup(resp.text, 'html.parser')
            form_value_element = soup.find(id="form_value")
            
            if not form_value_element:
                return {"success": False, "error": "form_value not found. Site served a bot-check page."}

            # 2. Prepare Payload
            payload = json.loads(form_value_element.text)
            payload["text[]"] = [text]
            
            # 3. POST request to create image
            post_headers = headers.copy()
            post_headers.update({
                "Origin": "https://textpro.me",
                "Referer": url,
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            })

            # Convert dict to form-encoded string manually to ensure correct formatting
            post_resp = await client.post(
                "https://textpro.me/effect/create-image", 
                data=payload, 
                headers=post_headers
            )
            
            result = post_resp.json()
            if result.get("success"):
                return {
                    "success": True, 
                    "image_url": f"{payload['build_server']}{result['image']}"
                }
            return {"success": False, "message": result.get("message")}

        except Exception as e:
            return {"success": False, "error": str(e)}
