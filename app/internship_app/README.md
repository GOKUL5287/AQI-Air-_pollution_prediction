# Air Quality Index — Global Air & Ocean Intelligence Platform

> **Cinematic, scientifically responsible environmental intelligence platform combining a scroll-driven frame sequence, live OpenAQ ground telemetry, Open-Meteo weather forecasts, marine oceanographic reanalysis, and a verified machine-learning AQI prediction pipeline.**

---

## 1. Overview & Cinematic Reference

TerraPulse was built to bring real-world environmental science to life through a cinematic visual journey inspired by `videofile/Video Project 5.mp4`. As the user scrolls, a sequence of 227 image frames descends from outer space through clouds to continental landmasses, coastal waters, and localized monitoring stations.

### Key Highlights
- **Cinematic Earth & Atmosphere:** Scroll-scrubbed image sequence with a photorealistic Earth, cloud descent, coastal waters, and localized monitoring scenes.
- **Scroll-Controlled Descent:** GSAP + ScrollTrigger scrubbed timelines with cinematic typography reveals: *"Every breath tells a story"* $\to$ *"One planet. Many local stories."*
- **Synchronized Air Quality Telemetry:** Real-time OpenAQ v3 integration for criteria pollutants (PM2.5, PM10, NO₂, CO, SO₂, O₃) with standardized units.
- **Meteorological Coupling:** Live Open-Meteo weather observations and 72-hour forecasts (Temperature, Humidity, Wind speed & direction, Pressure, Precipitation).
- **Trained AQI Machine Learning Pipeline:** Scikit-learn model trained directly on the 13 verified features of `cleaned_AQI.csv` ($R^2 = 0.9988$, $\text{MAE} = 1.357$), running live inference alongside official EPA sub-index calculations.
- **Dedicated Ocean & Seawater Quality Intelligence:** Physical ocean dynamics (Sea Surface Temperature, wave height, wave period, current velocity) and Copernicus CMEMS biogeochemistry (Salinity, Dissolved Oxygen, ocean acidification pH, Chlorophyll-a). **Strictly isolated from the atmospheric AQI model.**
- **Interactive Global Exploration:** Seamless toggle between **3D Globe Mode** (with raycasted station pins) and **Interactive Flat Map Mode**, instant search autocomplete across countries, states, and cities.
- **Scientific Analytics:** High-performance Plotly charts for 72-hour forecasts, pollutant time series, observed-versus-predicted validation curves, and 7-day marine trends.
- **Integrated Seasonal Insights:** Historical city AQI, seasonal pollutant profiles, weather summaries, daily AQI calendar, and data-completeness charts in the main cinematic app.
- **Full-Screen Sensor Map:** A persistent map control opens a worldwide, full-screen OpenAQ sensor map with search, marker readings, mouse-wheel zoom, and touch pinch-to-zoom.

---

## 2. Animation Storyboard & Mapping Table

Based on frame-by-frame analysis of `Video Project 5.mp4`:

| Reference Scene | TerraPulse Equivalent | Scroll Action | Visual Transition |
|---|---|---|---|
| **Scene 1: Space & Stylized Earth** (0.0s – 1.5s) | **Earth from Space Hero** | `scroll: 0%` (Initial Viewport) | 3D Earth floating in deep space with Rayleigh scattering glow, rotating cloud deck, day/night terminator, and typography reveal: **TERRAPULSE — Global Air & Ocean Intelligence**. |
| **Scene 2: Atmospheric Descent** (1.5s – 3.5s) | **Scroll-Controlled Atmospheric Descent** | `scroll: 0% → 30%` | GSAP-scrubbed camera descent toward Earth, penetrating volumetric cloud particles with depth-of-field blur. Text reveals: *"Every breath tells a story"* $\to$ *"One planet. Many local stories."* |
| **Scene 3: 3D Map & Monuments** (3.5s – 5.0s) | **Interactive Geographic World Map** | `scroll: 30% → 55%` | Transition into interactive geographic view. Continental boundaries and country labels illuminate. Live AQI monitoring markers, wind vector overlays, and search controls appear. |
| **Scene 4: Ocean Descent** (5.0s – 7.0s) | **Dedicated Ocean & Seawater Intelligence** | `scroll: 55% → 75%` | Camera dives into the ocean realm with dynamic water caustics. Headline: *"The health of our planet goes deeper."* Dedicated ocean telemetry reveals SST, Salinity, Dissolved Oxygen, pH, Chlorophyll-a, and oceanic currents. |
| **Scene 5: Scholar's Sphere & Action** (7.0s – 7.57s) | **Environmental Command Center & Timeline** | `scroll: 75% → 100%` | Scientific command center: 72-hour interactive Plotly timeline, Country $\to$ State $\to$ City drilldown, ML-validated AQI predictions, and evidence-based health advisories: *"Understand the planet. Protect its future."* |

---

## 3. Project Architecture

```
internship_app/
├── backend/
│   ├── app.py                      # Flask REST API Server & static router
│   ├── models/
│   │   ├── aqi_lstm.pt             # Trained PyTorch LSTM AQI Regressor
│   │   ├── scaler.joblib           # Fitted StandardScaler on 13 features
│   │   └── model_metadata.json     # Feature schema, metrics, and training provenance
│   └── services/
│       ├── geography_service.py    # Global Country -> State -> City hierarchy & search
│       ├── weather_service.py      # Open-Meteo current & 72h forecast client
│       ├── air_quality_service.py  # OpenAQ v3 API client & ground station archive
│       ├── marine_quality_service.py # Open-Meteo Marine & Copernicus CMEMS reanalysis
│       ├── aqi_model_service.py    # ML inference & EPA sub-index calculation
│       └── health_advisory_service.py # WHO / EPA evidence-based health guidance
├── static/
│   ├── assets/
│   │   └── frames/                 # 227 scroll-scrubbed JPG frames
│   ├── css/
│   │   └── styles.css              # Design tokens, glassmorphism, responsive styles
│   └── js/
│       └── app.js                  # Main controller, frame engine, GSAP, Plotly charts
├── templates/
│   └── index.html                  # Full semantic HTML5 single-page application
├── videofile/
│   └── Video Project 5.mp4         # Visual reference video
├── .env.example                    # Environment variable configuration template
├── requirements.txt                # Python dependencies
├── run_app.py                      # Root launcher script
└── README.md                       # Complete documentation
```

---

## 4. Machine Learning Model & Preprocessing Pipeline

- **Training Dataset:** `cleaned_AQI.csv` (904,010 records combining OpenAQ ground observations with Open-Meteo meteorological factors).
- **Features (13 verified environmental inputs in exact order):**
  1. `PM2.5` (µg/m³)
  2. `PM10` (µg/m³)
  3. `NO2` (µg/m³)
  4. `CO` (mg/m³)
  5. `SO2` (µg/m³)
  6. `O3` (µg/m³)
  7. `Temperature_C` (°C)
  8. `Relative_Humidity_pct` (%)
  9. `Wind_Speed_kmh` (km/h)
  10. `Hour` (0–23)
  11. `DayOfWeek` (0–6)
  12. `Month` (1–12)
  13. `DayOfYear` (1–366)
- **Model Framework:** PyTorch `LSTM` (2 recurrent layers, 24-hour input sequence)
- **Scaler:** `StandardScaler`
- **Evaluation Results on 12,000 Held-Out Sequences:**
  - **$R^2$ Score:** `0.6618`
  - **Mean Absolute Error (MAE):** `17.642` AQI points
  - **Root Mean Squared Error (RMSE):** `33.714` AQI points

---

## 5. API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `GET /api/regions/countries` | `GET` | List all supported countries and summary telemetry. |
| `GET /api/regions/<country>/states` | `GET` | List states/provinces for a given country code. |
| `GET /api/regions/<country>/stations?page=1&limit=1000&state=` | `GET` | Page through OpenAQ monitoring locations by country and provider-supplied locality. |
| `GET /api/regions/stations?page=1&limit=1000` | `GET` | Page through worldwide OpenAQ monitoring locations with coordinates and available sensor types. |
| `GET /api/regions/<country>/cities` | `GET` | List built-in reference cities for a country. |
| `GET /api/regions/search?q={query}` | `GET` | Autocomplete search across countries, states, and stations. |
| `GET /api/weather/current?lat=&lon=` | `GET` | Real-time Open-Meteo weather variables. |
| `GET /api/weather/forecast?lat=&lon=&hours=72` | `GET` | 72-hour hourly weather forecast. |
| `GET /api/air-quality/live-status` | `GET` | Reports whether an OpenAQ key is configured (never returns the key). |
| `GET /api/air-quality/current?lat=&lon=&station_id=&refresh=1` | `GET` | Latest OpenAQ station pollutants; `refresh=1` bypasses the server cache. |
| `GET /api/air-quality/history?lat=&lon=&hours=24` | `GET` | 24-hour historical pollutant trend. |
| `POST /api/aqi/predict` | `POST` | Execute ML inference on custom 13-feature inputs. |
| `GET /api/aqi/timeline-forecast?lat=&lon=&hours=72` | `GET` | 72-hour ML-predicted AQI timeline with weather inputs. |
| `GET /api/marine/current?lat=&lon=` | `GET` | Physical ocean dynamics and Copernicus biogeochemistry. |
| `GET /api/marine/history?lat=&lon=&days=7` | `GET` | 7-day marine time series (SST, salinity, DO, pH). |
| `GET /api/health/advisory?aqi=&dominant_pollutant=` | `GET` | Evidence-based health guidance and alerts. |
| `GET /api/model/metadata` | `GET` | Model hyperparameters, training provenance, and evaluation metrics. |
| `GET /api/station/overview?lat=&lon=&station_id=` | `GET` | Complete synchronized telemetry payload for any location. |
| `GET /api/analytics/seasonal?city=&year=` | `GET` | Historical AQI, seasonal pollutant and weather summaries, daily AQI, and data completeness for a city. |

---

## 6. Quick Start & Installation

### Prerequisites
- Python 3.10+
- Modern WebGL-capable web browser (Chrome, Edge, Firefox, Safari)

### Setup Instructions
1. **Navigate to the repository root:**
   ```bash
   cd AQI-Air-_pollution_prediction
   ```

2. **Create an app environment and install dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r app/internship_app/requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp app/internship_app/.env.example app/internship_app/.env
   ```
   Set `OPENAQ_API_KEY` in `.env` to enable live global country and station data. Without a key, the app uses a small built-in reference list; baseline pollutant inputs are labeled as fallback, not as observed readings. Open-Meteo requires no API key.

   The sticky map shows the curated city locations (the original compact map), rather than plotting every OpenAQ station at once. Open a city marker to request the latest nearby OpenAQ sensor measurements. The popup's **Open seasonal dashboard** action closes the map and scrolls to Seasonal Insights, selecting the matching historical city when available. Readings are fetched on demand (not for every marker), cached for 15 minutes, and can be explicitly refreshed from the popup. Marker colors indicate whether a live observation is available; they do not represent an AQI category. Without an OpenAQ key, the map clearly labels reference/demo data and does not present it as live.

   Seasonal Insights reads `data/station_hour_merged.parquet` from the repository root by default. Set `AQI_HISTORY_PATH` in `.env` if the file is elsewhere. The dashboard reports a clear unavailable state if the history file is missing.

4. **Launch TerraPulse:**
   ```bash
   cd app/internship_app
   python run_app.py
   ```

5. **Open in Browser:**
   Navigate to:
   ```
   http://localhost:5000
   ```

---

## 7. Data Provenance & Transparency Standards

The Seasonal Insights panel uses city-filtered station-hour records from
`station_hour_merged.parquet`. Seasonal pollutant profiles are normalized
against each pollutant's own all-season mean; they are not AQI sub-indices or
cross-pollutant health-risk rankings. Daily AQI values are means of available
station-hour observations. Missing dates and readings remain visibly missing.
The weather and pollution summaries are descriptive associations and do not
establish health causation.

Every data point in the user interface displays an official provenance badge:
- `OBSERVED`: Live ground-station monitoring measurement.
- `WEATHER FORECAST`: Provider-calculated meteorological model output.
- `MODEL PREDICTION`: TerraPulse machine-learning inferred value.
- `HISTORICAL`: Verified historical ground truth records.
- `COPERNICUS_REANALYSIS`: Satellite / ocean model reanalysis for marine biogeochemistry.
- `DEMONSTRATION`: Verified fallback test scenarios when live sensors are offline.
- `UNAVAILABLE`: Explicitly shown when a station has missing sensors.
