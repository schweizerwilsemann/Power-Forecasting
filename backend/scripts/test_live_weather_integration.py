import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.container import Container
from app.infrastructure.services.weather_service import OpenWeatherService

def test_integration():
    try:
        print("Initializing Container...")
        container = Container()
        
        service = container.forecasting_service
        
        print("Calling forecast_next(horizon=1, use_live_weather=True)...")
        # Note: forecast_next in my updated code takes use_live_weather
        result = service.forecast_next(horizon=1, include_components=False, use_live_weather=True)
        
        print("Result:")
        print(result)
        
        if result.get('source') == 'live_weather':
            print("✅ SUCCESS: Source is live_weather")
            print(f"Predicted Energy: {result['prediction_wh']} Wh")
        else:
            print("⚠️  FAILURE: Source is not live_weather. Falling back to history?")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_integration()
