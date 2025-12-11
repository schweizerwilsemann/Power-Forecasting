from __future__ import annotations

import os
import requests
from typing import Optional, Dict, Any

class OpenWeatherService:
    """Service to fetch real-time weather data from OpenWeatherMap."""

    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self, api_key: str):
        self.api_key = api_key
        # Default location: Central Europe (East Germany approx based on analysis)
        # 17.8E is closer to Poland, but let's use a generic central location or what User found.
        # User found 105.84/21.02 for Hanoi in their example, but approved Germany.
        # Let's default to Kassel, Germany (Indices often use this) or the estimated 17.8E
        # Lat for Germany is ~51.
        self.default_lat = 51.1
        self.default_lon = 17.8 

    def get_current_weather(self, lat: Optional[float] = None, lon: Optional[float] = None) -> Dict[str, Any]:
        """Fetch current weather data."""
        params = {
            "lat": lat if lat is not None else self.default_lat,
            "lon": lon if lon is not None else self.default_lon,
            "appid": self.api_key,
            "units": "metric"
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            # In a real app, log this
            print(f"Error fetching weather: {e}")
            raise ValueError(f"Failed to fetch weather data: {e}")
