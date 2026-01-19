from fastapi import FastAPI
import cloudscraper
import json
from bs4 import BeautifulSoup

app = FastAPI()

def generate_textpro(effect_url, user_text):
    # 1. Start a session ggggg
    scraper = cloudscraper.create_scraper()
    
    # 2. Get the effect page
    response = scraper.get(effect_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 3. Find the "form_value" element you discovered
    form_value_element = soup.find(id="form_value")
    
    if not form_value_element:
        return {"success": False, "error": "Could not find form_value. The site might be blocking this request."}
    
    # 4. Parse the JSON inside that element
    # This contains the ID, Token, Sign, and Build Server automatically!
    payload = json.loads(form_value_element.text)
    
    # 5. Overwrite the text field with the user's input
    # TextPro usually uses "text[]" as the key for the input text
    payload["text[]"] = [user_text]
    
    # 6. Send the POST request to the endpoint
    post_url = "https://textpro.me/effect/create-image"
    headers = {
        "Referer": effect_url,
        "X-Requested-With": "XMLHttpRequest"
    }
    
    result_raw = scraper.post(post_url, data=payload, headers=headers)
    
    if result_raw.status_code == 200:
        res_json = result_raw.json()
        if res_json.get("success"):
            # Construct the full image URL
            full_url = f"{payload['build_server']}{res_json['image']}"
            return {"success": True, "image_url": full_url}
        else:
            return {"success": False, "message": res_json.get("message")}
            
    return {"success": False, "error": f"Server returned {result_raw.status_code}"}

@app.get("/generate")
def api_endpoint(url: str, text: str):
    return generate_textpro(url, text)
