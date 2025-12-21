import requests
import json

# 1. CONFIGURATION
# Paste your Apps Script Web App URL here
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwI79TvHGc9shdXx9_Writ1R5s_CiIb6jpQxRcaAFUE0gCvekUYE1ZwVD0y1rIEjd2sUQ/exec"

def test_connection():
    print("🔵 Starting Connection Test...")

    # 2. DUMMY DATA
    # This mimics the exact structure your Agent will produce
    payload = {
        "question": "TEST [Integration Check]: If a car travels 100km in 2 hours, what is the speed?",
        "op1": "20 km/hr",
        "op2": "40 km/hr",
        "op3": "50 km/hr",  # This is the correct one
        "op4": "60 km/hr",
        "correct option": "50 km/hr", # MUST MATCH op3 EXACTLY (Case sensitive)
        "explanation of option": "Speed = Distance / Time. Therefore, 100 / 2 = 50."
    }

    # 3. SEND REQUEST
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(APPS_SCRIPT_URL, json=payload, headers=headers)
        
        # 4. ANALYZE RESPONSE
        if response.status_code == 200:
            print("✅ SUCCESS: Server responded 200 OK")
            print(f"   Response Body: {response.text}")
            print("👉 NOW GO CHECK YOUR GOOGLE FORM!")
        else:
            print(f"❌ FAILED: Status Code {response.status_code}")
            print(f"   Error Message: {response.text}")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")

if __name__ == "__main__":
    test_connection()
