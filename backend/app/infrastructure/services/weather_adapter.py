from __future__ import annotations

import math
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any

class WeatherAdapter:
    """Adapts external weather API data to the Application's feature schema."""

    # Model expected columns (subset)
    # ['temp', 'humidity', 'wind_speed', 'GHI', 'clouds_all', 'rain_1h', 'snow_1h', 'sunlightTime', 'SunlightTime/daylength']

    def to_model_input(self, api_response: Dict[str, Any]) -> pd.DataFrame:
        """
        Convert OpenWeatherMap (OWM) response to a single-row DataFrame 
        compatible with the model's feature engineering.
        """
        
        # 1. Basic Extraction
        main = api_response.get('main', {})
        wind = api_response.get('wind', {})
        clouds = api_response.get('clouds', {})
        rain = api_response.get('rain', {})
        snow = api_response.get('snow', {})
        sys = api_response.get('sys', {})
        
        # Timestamp
        dt = api_response.get('dt')
        timestamp = datetime.fromtimestamp(dt, tz=timezone.utc) if dt else datetime.now(timezone.utc)
        
        # 2. Map direct features
        data = {
            'Time': timestamp,
            'temp': main.get('temp'),
            'pressure': main.get('pressure'),
            'humidity': main.get('humidity'),
            'wind_speed': wind.get('speed'),
            'clouds_all': clouds.get('all', 0),
            'rain_1h': rain.get('1h', 0),
            'snow_1h': snow.get('1h', 0),
        }
        
        # 3. Solar Calculations
        # Need Lat/Lon for Solar Zenith
        lat = api_response.get('coord', {}).get('lat', 51.1)
        lon = api_response.get('coord', {}).get('lon', 17.8)
        
        ghi_estimated = self._estimate_ghi(timestamp, lat, lon, data['clouds_all'])
        data['GHI'] = ghi_estimated
        
        # 4. Sun Time Features
        sunrise = sys.get('sunrise')
        sunset = sys.get('sunset')
        
        if sunrise and sunset:
            day_length_sec = sunset - sunrise
            # Simple logic: SunlightTime is currently available daylight minutes?
            # Or is it total daylight for the day?
            # In training data, 'sunlightTime' seems to be accumulating minutes of sun or day length.
            # Checking 'SunlightTime/daylength', usually it's a ratio.
            # Let's look at Training Data logic or feature_engineering.py
            # feature_engineering.py doesn't calculate 'sunlightTime', it expects it.
            # In many datasets, sunlightTime might be "minutes of sunshine" (duration).
            # For a snapshot, this is hard.
            # However, looking at feature_engineering.py:
            # df['SunlightTime/daylength'] is used.
            # If we are in "simulation", we can approximate:
            # If (current_time > sunrise and current_time < sunset):
            #   We are in sunlight.
            # But the feature is likely "Potential sunlight minutes" or similar.
            # Let's approximate 'sunlightTime' as DayLength (in minutes) * (1 - CloudCover/100)?
            # Or just DayLength in minutes.
            # Let's recalculate based on typical csv values.
            # In CSV sample line 1: sunlightTime=780, dayLength=825. Ratio=0.95.
            # So sunlightTime is < dayLength. Likely "Clear sky minutes".
            
            day_length_min = day_length_sec / 60
            data['dayLength'] = day_length_min # Helper, might be dropped
            
            # Estimate sunlightTime based on clouds
            # If 0 clouds, sunlightTime = dayLength
            # If 100 clouds, sunlightTime = 0
            # Linear interp
            data['sunlightTime'] = day_length_min * (1 - (data['clouds_all'] / 100))
            
            # Ratio
            data['SunlightTime/daylength'] = data['sunlightTime'] / day_length_min if day_length_min > 0 else 0
        else:
            data['sunlightTime'] = 0
            data['SunlightTime/daylength'] = 0

        # Create DataFrame
        df = pd.DataFrame([data])
        return df

    def _estimate_ghi(self, dt: datetime, lat: float, lon: float, cloud_cover_percent: float) -> float:
        """
        Estimate Global Horizontal Irradiance (GHI) using solar geometry and cloud cover.
        Theory: GHI = ClearSky_GHI * Cloud_Attenuation
        """
        # 1. Conversions
        lat_rad = math.radians(lat)
        
        # Day of year
        doy = dt.timetuple().tm_yday
        
        # 2. Solar Declination (delta) - approximate
        # angle of sun relative to equatorial plane
        delta = math.radians(23.45 * math.sin(math.radians(360/365 * (doy - 81))))
        
        # 3. Equation of Time (EoT) - minutes
        # Correction between solar time and clock time
        b = math.radians(360/364 * (doy - 81))
        eot = 9.87 * math.sin(2*b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
        
        # 4. Solar Time (Local Solar Time)
        # UTC hour + Lon_offset + EoT
        # Time in decimal hours
        utc_hour = dt.hour + dt.minute/60.0
        
        # Local Solar Time (LST) in hours
        lst = utc_hour + (lon / 15.0) + (eot / 60.0)
        
        # Hour Angle (omega)
        # 15 degrees per hour from solar noon (12:00)
        omega = math.radians(15 * (lst - 12))
        
        # 5. Solar Zenith Angle (theta_z)
        # cos(theta_z) = sin(lat)*sin(delta) + cos(lat)*cos(delta)*cos(omega)
        cos_theta_z = math.sin(lat_rad)*math.sin(delta) + math.cos(lat_rad)*math.cos(delta)*math.cos(omega)
        
        # Limit to 0 (Sun is down)
        cos_theta_z = max(0, cos_theta_z)
        
        if cos_theta_z <= 0:
            return 0.0 # Night
            
        # 6. Clear Sky Model (Simplified Adnot or Kasten)
        # GHI_clear = 910 * cos(theta_z) + 30 (Very rough)
        # Better: GHI_clear = I_sc * cos(theta_z) * transmission
        # I_sc = 1367 W/m2
        # A clearer simpler model: 
        # Ryan-Stolzenbach: GHI = 1120 * cos(theta_z)^0.7 (approx)
        ghi_clear = 1000 * cos_theta_z ** 1.15
        
        # 7. Cloud Attenuation
        # Octas model or similar. 
        # C = cloud_cover fraction (0-1)
        # Transmission = 1 - 0.75 * C^3.4
        c = cloud_cover_percent / 100.0
        attenuation = 1 - 0.75 * (c ** 3)
        
        ghi = ghi_clear * attenuation
        return max(0.0, ghi)
