"""
TerraPulse Weather Service
Integrates Open-Meteo API for real-time observations and up to 72-hour forecasts.
Provides meteorological variables aligned with the TerraPulse ML AQI inference pipeline.
"""

import time
import requests
from typing import Dict, Any, Optional

class WeatherService:
    CACHE_TTL_CURRENT = 900   # 15 minutes
    CACHE_TTL_FORECAST = 1800 # 30 minutes
    _cache: Dict[str, Any] = {}

    @classmethod
    def get_current_weather(cls, lat: float, lon: float) -> Dict[str, Any]:
        cache_key = f"current_{lat:.3f}_{lon:.3f}"
        now = time.time()

        if cache_key in cls._cache:
            entry = cls._cache[cache_key]
            if now - entry["timestamp"] < cls.CACHE_TTL_CURRENT:
                return entry["data"]

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "surface_pressure",
                "wind_speed_10m",
                "wind_direction_10m",
                "precipitation",
                "cloud_cover"
            ],
            "wind_speed_unit": "kmh",
            "timezone": "auto"
        }

        try:
            resp = requests.get(url, params=params, timeout=(2.0, 3.0))
            if resp.status_code == 200:
                data = resp.json()
                current = data.get("current", {})
                units = data.get("current_units", {})

                result = {
                    "temperature_c": current.get("temperature_2m"),
                    "relative_humidity_pct": current.get("relative_humidity_2m"),
                    "surface_pressure_hpa": current.get("surface_pressure"),
                    "wind_speed_kmh": current.get("wind_speed_10m"),
                    "wind_direction_deg": current.get("wind_direction_10m"),
                    "precipitation_mm": current.get("precipitation"),
                    "cloud_cover_pct": current.get("cloud_cover"),
                    "observation_time": current.get("time"),
                    "coordinates": {"lat": lat, "lon": lon},
                    "provenance": "WEATHER_FORECAST",
                    "provider": "Open-Meteo High-Resolution Weather API",
                    "status": "LIVE"
                }

                cls._cache[cache_key] = {"timestamp": now, "data": result}
                return result
        except Exception as e:
            pass

        # Fallback realistic weather baseline if network is temporarily unavailable
        fallback = {
            "temperature_c": 22.4,
            "relative_humidity_pct": 58.0,
            "surface_pressure_hpa": 1013.2,
            "wind_speed_kmh": 12.5,
            "wind_direction_deg": 180,
            "precipitation_mm": 0.0,
            "cloud_cover_pct": 25.0,
            "observation_time": time.strftime("%Y-%m-%dT%H:00"),
            "coordinates": {"lat": lat, "lon": lon},
            "provenance": "DEMONSTRATION",
            "provider": "Climatological Reference Fallback",
            "status": "FALLBACK"
        }
        return fallback

    @classmethod
    def get_forecast(cls, lat: float, lon: float, hours: int = 72) -> Dict[str, Any]:
        hours = max(12, min(hours, 72))
        cache_key = f"forecast_{lat:.3f}_{lon:.3f}_{hours}"
        now = time.time()

        if cache_key in cls._cache:
            entry = cls._cache[cache_key]
            if now - entry["timestamp"] < cls.CACHE_TTL_FORECAST:
                return entry["data"]

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": [
                "temperature_2m",
                "relative_humidity_2m",
                "surface_pressure",
                "wind_speed_10m",
                "wind_direction_10m",
                "precipitation_probability",
                "cloud_cover"
            ],
            "forecast_days": 4, # gives up to 96 hours
            "wind_speed_unit": "kmh",
            "timezone": "auto"
        }

        try:
            resp = requests.get(url, params=params, timeout=(2.0, 3.0))
            if resp.status_code == 200:
                data = resp.json()
                hourly = data.get("hourly", {})
                times = hourly.get("time", [])[:hours]

                timeline = []
                for i in range(len(times)):
                    timeline.append({
                        "time": times[i],
                        "temperature_c": hourly.get("temperature_2m", [])[i],
                        "relative_humidity_pct": hourly.get("relative_humidity_2m", [])[i],
                        "surface_pressure_hpa": hourly.get("surface_pressure", [])[i],
                        "wind_speed_kmh": hourly.get("wind_speed_10m", [])[i],
                        "wind_direction_deg": hourly.get("wind_direction_10m", [])[i],
                        "precipitation_probability_pct": hourly.get("precipitation_probability", [])[i],
                        "cloud_cover_pct": hourly.get("cloud_cover", [])[i]
                    })

                result = {
                    "horizon_hours": len(timeline),
                    "timeline": timeline,
                    "coordinates": {"lat": lat, "lon": lon},
                    "provenance": "WEATHER_FORECAST",
                    "provider": "Open-Meteo GFS/ECMWF Ensemble API",
                    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "status": "LIVE"
                }

                cls._cache[cache_key] = {"timestamp": now, "data": result}
                return result
        except Exception:
            pass

        # Robust synthetic 72h forecast if offline
        import datetime
        timeline = []
        base_dt = datetime.datetime.now()
        for h in range(hours):
            dt = base_dt + datetime.timedelta(hours=h)
            hour = dt.hour
            temp = 18.0 + 7.0 * np.sin((hour - 8) * np.pi / 12) if 'np' in globals() else 21.0
            timeline.append({
                "time": dt.strftime("%Y-%m-%dT%H:00"),
                "temperature_c": round(20.0 + 5.0 * ((hour % 12) / 6.0 - 1.0), 1),
                "relative_humidity_pct": round(65.0 - 15.0 * ((hour % 12) / 6.0 - 1.0), 1),
                "surface_pressure_hpa": 1012.5,
                "wind_speed_kmh": round(10.0 + (h % 5), 1),
                "wind_direction_deg": (180 + h * 5) % 360,
                "precipitation_probability_pct": 10,
                "cloud_cover_pct": 30
            })

        return {
            "horizon_hours": len(timeline),
            "timeline": timeline,
            "coordinates": {"lat": lat, "lon": lon},
            "provenance": "DEMONSTRATION",
            "provider": "Synthetic Atmospheric Timeline",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "FALLBACK"
        }
