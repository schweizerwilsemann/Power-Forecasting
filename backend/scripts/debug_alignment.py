import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import traceback

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.container import Container

def check_alignment():
    container = Container()
    service = container.forecasting_service
    
    print("--- Inspecting Time Travel Alignment ---")
    
    # Load History directly to check end time
    history_df = service._history_gateway.load(limit=5)
    last_hist_time = pd.to_datetime(history_df['Time'].iloc[-1]).tz_convert('UTC')
    print(f"Last Historical Timestamp: {last_hist_time}")
    
    # Get Current Live Weather Time
    # We simulate what the service does
    try:
        api_data = service._weather_service.get_current_weather()
        future_df = service._weather_adapter.to_model_input(api_data)
        current_time = pd.to_datetime(future_df['Time'].iloc[0]).tz_convert('UTC')
        print(f"Current Live Timestamp:    {current_time}")
        
        # Calculate naive gap
        gap = current_time - last_hist_time
        print(f"Raw Gap: {gap}")
        
        # Calculate what Time Travel does
        if gap > pd.Timedelta(hours=2):
            offset = gap - pd.Timedelta(minutes=15)
            shifted_last_hist = last_hist_time + offset
            print(f"Shifted Last History Time: {shifted_last_hist}")
            print(f"Target (Current) Time:     {current_time}")
            
            # Check Time of Day mismatch
            hist_hour = last_hist_time.hour
            curr_hour = current_time.hour
            print(f"Original Hist Hour: {hist_hour}")
            print(f"Current Live Hour:  {curr_hour}")
            
            if hist_hour != curr_hour:
                print("\n⚠️  MISALIGNMENT DETECTED!")
                print("We are shifting data from a different time-of-day to be adjacent to now.")
                print(f"Model sees: {hist_hour}:00 data -> followed immediately by -> {curr_hour}:00 data.")
                print("This creates massive artifacts in lag features (e.g., Sun -> Dark in 15 mins).")
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    check_alignment()
