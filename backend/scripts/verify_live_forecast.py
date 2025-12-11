import sys
import requests
import json
from pathlib import Path

# Add backend to path using relative path
sys.path.append(str(Path(__file__).resolve().parents[1]))

def verify():
    url = "http://localhost:8000/forecast/next"
    
    # 1. LIVE REQUEST
    print("\n--- TEST 1: LIVE WEATHER ---")
    payload_live = {
        "horizon": 4,
        "includeComponents": False,
        "useLiveWeather": True
    }
    try:
        resp = requests.post(url, json=payload_live)
        if resp.status_code == 200:
            data = resp.json()
            val_live = data.get('prediction_wh')
            src_live = data.get('source')
            print(f"Prediction: {val_live}")
            print(f"Source: {src_live} (Expected: live_weather)")
        else:
            print(f"Error: {resp.status_code} - {resp.text}")
            val_live = None
    except Exception as e:
        print(f"Exception: {e}")
        val_live = None

    # 2. HISTORY REQUEST
    print("\n--- TEST 2: HISTORY (SIMULATION) ---")
    payload_hist = {
        "horizon": 4,
        "includeComponents": False,
        "useLiveWeather": False
    }
    try:
        resp = requests.post(url, json=payload_hist)
        if resp.status_code == 200:
            data = resp.json()
            val_hist = data.get('prediction_wh')
            src_hist = data.get('source')
            print(f"Prediction: {val_hist}")
            print(f"Source: {src_hist} (Expected: historical_simulation)")
        else:
            print(f"Error: {resp.status_code} - {resp.text}")
            val_hist = None
    except Exception as e:
        print(f"Exception: {e}")
        val_hist = None

    # COMPARISON
    print("\n--- CONCLUSION ---")
    if val_live is not None and val_hist is not None:
        if val_live == val_hist:
            print("❌ FAILURE: Live and History values are IDENTICAL. Live weather logic likely falling back to history.")
            print(f"Value: {val_live}")
        else:
            print("✅ SUCCESS: Live and History values are DIFFERENT.")
            print(f"Live: {val_live} | History: {val_hist}")
    else:
        print("⚠️  Cannot compare due to errors.")

if __name__ == "__main__":
    verify()
