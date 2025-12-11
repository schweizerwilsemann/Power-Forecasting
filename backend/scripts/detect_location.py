import pandas as pd
import numpy as np

def analyze_location(csv_path):
    try:
        df = pd.read_csv(csv_path)
        df['Time'] = pd.to_datetime(df['Time'], utc=True)
        
        # Filter for days with clear solar profiles (high GHI) to get accurate sunrise/sunset
        # We assume GHI > 0 means sun is up.
        df['is_day'] = df['GHI'] > 5  # low threshold
        
        # Group by date
        daily = df.groupby(df['Time'].dt.date).agg({
            'GHI': 'max',
            'is_day': 'sum', # 15 min intervals
            'temp': 'mean'
        })
        
        # Find Solar Noon: Time of max GHI averaged
        # We need the original time for this
        df['hour_minute'] = df['Time'].dt.hour * 60 + df['Time'].dt.minute
        
        # Get index of max GHI per day
        idx_max_ghi = df.groupby(df['Time'].dt.date)['GHI'].idxmax()
        solar_noons = df.loc[idx_max_ghi, 'Time']
        
        # Average UTC hour of solar noon
        avg_noon_utc = solar_noons.dt.hour.mean() + solar_noons.dt.minute.mean()/60.0
        
        # Longitude estimation:
        # Solar noon at UTC 12:00 -> Lon 0
        # Earth rotates 15 degrees per hour.
        # If noon is at 5:00 UTC -> It happened 7 hours early? No.
        # Noon = 12:00 Local Solar Time.
        # Lon = (12 - Noon_UTC) * 15
        estimated_lon = (12 - avg_noon_utc) * 15
        
        print(f"Average Solar Noon (UTC): {avg_noon_utc:.2f}h")
        print(f"Estimated Longitude: {estimated_lon:.2f} degrees")
        
        # Latitude estimation (Day length variance)
        # 1 step = 15 mins
        max_day_steps = daily['is_day'].max()
        min_day_steps = daily['is_day'].min()
        
        max_day_hours = max_day_steps * 15 / 60
        min_day_hours = min_day_steps * 15 / 60
        
        print(f"Max Day Length: {max_day_hours:.2f} hours")
        print(f"Min Day Length: {min_day_hours:.2f} hours")
        print(f"Avg Temp: {df['temp'].mean():.2f}")
        
    except Exception as e:
        print(e)

from pathlib import Path

if __name__ == "__main__":
    analyze_location(Path(__file__).resolve().parents[2] / "Renewable.csv")
