from fastapi import FastAPI
import httpx
from bs4 import BeautifulSoup

app = FastAPI()

@app.get("/debug")
async def debug_connection(url: str):
    debug_info = {}
    try:
        async with httpx.AsyncClient(http2=True, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            }
            
            # 1. Test the GET request
            response = await client.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            debug_info["status_code"] = response.status_code
            debug_info["page_title"] = soup.title.string if soup.title else "No Title"
            debug_info["is_cloudflare"] = "cf-challenge" in response.text or "ray-id" in response.text
            debug_info["form_value_exists"] = soup.find(id="form_value") is not None
            
            # Show a tiny bit of the HTML body for visual confirmation
            debug_info["html_preview"] = response.text[:500].replace("\n", " ")

            # 2. Check the Vercel Region & IP (To see if Singapore is actually working)
            # This helps confirm if Vercel actually moved your function
            ip_check = await client.get("https://ifconfig.me/ip")
            debug_info["server_ip"] = ip_check.text

    except Exception as e:
        debug_info["error"] = str(e)

    return debug_info
