"""
TerraPulse — Cinematic Global Air & Ocean Intelligence Platform
Flask REST API Backend Server
"""

import os
import sys
from requests import RequestException
from flask import Flask, request, jsonify, send_from_directory, render_template

# Ensure backend folder is on python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.geography_service import GeographyService
from services.weather_service import WeatherService
from services.air_quality_service import AirQualityService
from services.marine_quality_service import MarineQualityService
from services.aqi_model_service import AQIModelService
from services.health_advisory_service import HealthAdvisoryService
from services.seasonal_analytics_service import get_seasonal_summary

app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static"),
    template_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
)

# CORS middleware for local API exploration
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    return response

# --- GEOGRAPHY ENDPOINTS ---

@app.route("/api/regions/countries", methods=["GET"])
def get_countries():
    countries = AirQualityService.get_openaq_countries()
    return jsonify({"status": "success", "data": countries, "total": len(countries)})

@app.route("/api/regions/stations", methods=["GET"])
def get_global_stations():
    try:
        result = AirQualityService.get_openaq_global_locations(
            page=request.args.get("page", 1, type=int),
            limit=request.args.get("limit", 1000, type=int),
        )
        return jsonify({"status": "success", **result})
    except (RequestException, ValueError, RuntimeError, TypeError) as error:
        return jsonify({"status": "error", "message": f"Unable to load global OpenAQ stations: {error}"}), 502

@app.route("/api/regions/<country_code>/states", methods=["GET"])
def get_states(country_code):
    try:
        localities = AirQualityService.get_openaq_localities(country_code)
        states = [{"code": locality, "name": locality} for locality in localities]
    except Exception:
        states = GeographyService.get_states(country_code)
    return jsonify({"status": "success", "country_code": country_code.upper(), "data": states, "total": len(states)})

@app.route("/api/regions/<country_code>/stations", methods=["GET"])
def get_country_stations(country_code):
    try:
        result = AirQualityService.get_openaq_locations(
            country_code,
            page=request.args.get("page", 1, type=int),
            limit=request.args.get("limit", 1000, type=int),
            locality=request.args.get("state"),
        )
        return jsonify({"status": "success", **result})
    except Exception as error:
        return jsonify({"status": "error", "message": f"Unable to load OpenAQ stations: {error}"}), 502

@app.route("/api/regions/<country_code>/cities", methods=["GET"])
def get_cities(country_code):
    state_code = request.args.get("state")
    cities = GeographyService.get_cities(country_code, state_code)
    return jsonify({"status": "success", "country_code": country_code.upper(), "state_code": state_code, "data": cities, "total": len(cities)})

@app.route("/api/regions/search", methods=["GET"])
def search_regions():
    q = request.args.get("q", "")
    results = GeographyService.search(q)
    return jsonify({"status": "success", "query": q, "results": results})

# --- WEATHER ENDPOINTS ---

@app.route("/api/weather/current", methods=["GET"])
def get_current_weather():
    lat = float(request.args.get("lat", 28.6139))
    lon = float(request.args.get("lon", 77.2090))
    weather = WeatherService.get_current_weather(lat, lon)
    return jsonify({"status": "success", "data": weather})

@app.route("/api/weather/forecast", methods=["GET"])
def get_weather_forecast():
    lat = float(request.args.get("lat", 28.6139))
    lon = float(request.args.get("lon", 77.2090))
    hours = int(request.args.get("hours", 72))
    forecast = WeatherService.get_forecast(lat, lon, hours)
    return jsonify({"status": "success", "data": forecast})

# --- AIR QUALITY ENDPOINTS ---

@app.route("/api/air-quality/live-status", methods=["GET"])
def get_air_quality_live_status():
    return jsonify({
        "status": "success",
        "live_available": bool(AirQualityService.API_KEY),
        "provider": "OpenAQ v3",
    })

@app.route("/api/air-quality/current", methods=["GET"])
def get_current_air_quality():
    lat = float(request.args.get("lat", 28.6139))
    lon = float(request.args.get("lon", 77.2090))
    station_id = request.args.get("station_id")
    refresh = request.args.get("refresh") == "1"
    if refresh:
        aq_data = AirQualityService.get_station_air_quality(
            lat, lon, station_id, force_refresh=True
        )
    else:
        aq_data = AirQualityService.get_station_air_quality(lat, lon, station_id)
    return jsonify({"status": "success", "data": aq_data})

@app.route("/api/air-quality/history", methods=["GET"])
def get_air_quality_history():
    lat = float(request.args.get("lat", 28.6139))
    lon = float(request.args.get("lon", 77.2090))
    station_id = request.args.get("station_id")
    hours = int(request.args.get("hours", 24))
    history = AirQualityService.get_historical_trends(lat, lon, station_id, hours)
    return jsonify({"status": "success", "data": history})

# --- ML MODEL INFERENCE & TIMELINE FORECAST ---

@app.route("/api/model/metadata", methods=["GET"])
def get_model_metadata():
    meta = AQIModelService.get_metadata()
    return jsonify({"status": "success", "data": meta})

@app.route("/api/aqi/predict", methods=["POST"])
def predict_aqi():
    req_data = request.get_json(force=True, silent=True) or {}
    try:
        prediction = AQIModelService.predict(req_data)
        return jsonify({"status": "success", "data": prediction})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/api/aqi/timeline-forecast", methods=["GET"])
def get_aqi_timeline_forecast():
    lat = float(request.args.get("lat", 28.6139))
    lon = float(request.args.get("lon", 77.2090))
    station_id = request.args.get("station_id")
    hours = int(request.args.get("hours", 72))

    aq = AirQualityService.get_station_air_quality(lat, lon, station_id)
    wx_forecast = WeatherService.get_forecast(lat, lon, hours)
    timeline = wx_forecast.get("timeline", [])

    predictions = AQIModelService.forecast_aqi_timeline(aq["measurements"], timeline)
    return jsonify({
        "status": "success",
        "station_id": aq["station_id"],
        "coordinates": {"lat": lat, "lon": lon},
        "horizon_hours": len(predictions),
        "timeline": predictions
    })

# --- MARINE QUALITY ENDPOINTS ---

@app.route("/api/marine/current", methods=["GET"])
def get_current_marine():
    lat = float(request.args.get("lat", 19.0760))
    lon = float(request.args.get("lon", 72.8777))
    marine = MarineQualityService.get_marine_quality(lat, lon)
    return jsonify({"status": "success", "data": marine})

@app.route("/api/marine/history", methods=["GET"])
def get_marine_history():
    lat = float(request.args.get("lat", 19.0760))
    lon = float(request.args.get("lon", 72.8777))
    days = int(request.args.get("days", 7))
    history = MarineQualityService.get_marine_history(lat, lon, days)
    return jsonify({"status": "success", "data": history})

# --- HEALTH ADVISORY ENDPOINT ---

@app.route("/api/health/advisory", methods=["GET"])
def get_health_advisory():
    aqi = float(request.args.get("aqi", 75.0))
    dominant = request.args.get("dominant_pollutant", "PM2.5")
    temp = float(request.args.get("temp_c", 22.0))
    advisory = HealthAdvisoryService.get_air_health_advisory(aqi, dominant, temp)
    return jsonify({"status": "success", "data": advisory})

# --- HISTORICAL SEASONAL ANALYTICS ---

@app.route("/api/analytics/seasonal", methods=["GET"])
def get_seasonal_analytics():
    city = request.args.get("city")
    year = request.args.get("year", type=int)
    try:
        summary = get_seasonal_summary(city, year)
        return jsonify({"status": "success", "data": summary})
    except FileNotFoundError as error:
        return jsonify({"status": "error", "message": str(error)}), 503
    except (RuntimeError, ValueError) as error:
        return jsonify({"status": "error", "message": str(error)}), 422

# --- COMPLETE STATION TELEMETRY OVERVIEW ---

@app.route("/api/station/overview", methods=["GET"])
def get_station_overview():
    lat = float(request.args.get("lat", 28.6139))
    lon = float(request.args.get("lon", 77.2090))
    station_id = request.args.get("station_id")

    # Fetch synchronous telemetry components
    aq = AirQualityService.get_station_air_quality(lat, lon, station_id)
    wx = WeatherService.get_current_weather(lat, lon)
    
    # Run ML prediction on the aligned inputs
    meas = aq["measurements"]
    ml_input = {
        "pm25": meas["pm25"], "pm10": meas["pm10"], "no2": meas["no2"],
        "co": meas["co"], "so2": meas["so2"], "o3": meas["o3"],
        "temperature_c": wx["temperature_c"],
        "relative_humidity_pct": wx["relative_humidity_pct"],
        "wind_speed_kmh": wx["wind_speed_kmh"]
    }
    prediction = AQIModelService.predict(ml_input)
    
    # Health guidance
    advisory = HealthAdvisoryService.get_air_health_advisory(
        prediction["predicted_aqi"],
        prediction["dominant_pollutant"],
        wx["temperature_c"]
    )
    
    # Marine quality if coastal
    marine = None
    is_coastal = request.args.get("is_coastal", "false").lower() == "true"
    if is_coastal or abs(lat) < 55: # evaluate marine conditions for coastal points
        marine = MarineQualityService.get_marine_quality(lat, lon)

    return jsonify({
        "status": "success",
        "station": {
            "station_id": aq["station_id"],
            "station_name": aq["station_name"],
            "city": aq.get("city", "Selected Location"),
            "country": aq.get("country", "Global"),
            "coordinates": {"lat": lat, "lon": lon},
            "is_coastal": is_coastal
        },
        "air_quality": aq,
        "weather": wx,
        "model_prediction": prediction,
        "health_advisory": advisory,
        "marine_intelligence": marine,
        "timestamp": wx["observation_time"]
    })

# --- FRONTEND ROUTING ---

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/seasonal-insights")
def seasonal_insights():
    streamlit_url = os.environ.get("SEASONAL_STREAMLIT_URL", "http://127.0.0.1:8501")
    separator = "&" if "?" in streamlit_url else "?"
    streamlit_url = f"{streamlit_url}{separator}embed=true"
    return render_template("seasonal_insights.html", streamlit_url=streamlit_url)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Air Quality Index backend on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
