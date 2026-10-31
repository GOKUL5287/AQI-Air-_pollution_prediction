# AQI Air Pollution Prediction

This repository contains two related but separate applications and an experimental AQI forecasting workflow:

1. **TerraPulse web application** — a Flask API and browser interface for air-quality, weather, marine, health-advisory, and model-prediction views. Its launcher also starts a separate Streamlit seasonal-analysis dashboard.
2. **Seasonal Health Dashboard** — a standalone Streamlit app analyzing pollutant, weather, and respiratory-pathogen records from its bundled CSV.
3. **Research pipeline** — notebooks and Python modules for building station-hour features and evaluating 24- and 48-hour AQI forecasts. It is not the model-serving path used by the Flask app.

The code distinguishes observed measurements, external weather forecasts, historical records, fallback/demo values, deterministic AQI calculations, and ML predictions. A prediction should not be treated as an observed AQI reading.


## 📎 Project Links

| Resource | Link |
|---|---|
| 📄 Project Report | [View the report](https://drive.google.com/file/d/1wsny5j2U-9BAJS5EjmddqHKVVZ6i_m7n/view?usp=sharing) |
| 🎥 Demo Video | [Watch the demo](https://drive.google.com/file/d/1ghdTti2g2004pKlMRjw6HrGr_AmQ9x8x/view?usp=drive_link) |

## Features

- Flask API and web UI with geographic search, station selection, AQI prediction, forecast timelines, and health guidance.
- OpenAQ v3 integration for station metadata and pollutant observations when an API key and network access are available.
- Open-Meteo weather and marine data requests, with explicit fallback behavior when requests are unavailable.
- Historical city and seasonal summaries from a station-hour Parquet dataset.
- Independent Streamlit analysis of pollutant/weather patterns and respiratory-pathogen records.
- Notebook and Python workflows for persistence, linear regression, histogram gradient boosting, PyTorch LSTM, and Prophet forecasting experiments.

## Architecture and execution flow

### TerraPulse web application

`app/internship_app/run_app.py` imports the Flask app, starts the Seasonal Health Dashboard as a Streamlit subprocess on port `8501` by default, then serves Flask on port `5000` by default. Flask routes in `backend/app.py` call service modules for geography, OpenAQ observations, weather, marine data, AQI predictions, seasonal history, and health guidance. The browser assets are served from `static/` and `templates/`.

The model service loads its artifacts lazily when a prediction, forecast, or metadata route is called. It expects `backend/models/aqi_lstm.pt` and `backend/models/scaler.joblib`; the checkpoint is a PyTorch state-dict package. **The scaler file is not present in this checkout, so model-dependent Flask routes currently fail to load.** Other Flask routes can operate independently, subject to their own data and network requirements.

### Seasonal Health Dashboard

`app/SeasonalHealthDashboard/app.py` reads its neighboring `final_merged_respiratory_satellite_data.csv` (or an uploaded CSV), then computes and displays seasonal summaries, correlations, and related charts. It does not import or use the Flask AQI model.

When launched by `run_app.py`, the dashboard is embedded through the Flask `/seasonal-insights` page. It can also be started independently.

### Research forecasting workflow

The research workflow is separate from the Flask model service. `src/features.py` builds station-specific lags, rolling statistics, calendar encodings, future targets, and temporal splits. `src/baselines.py` fits persistence, linear-regression, and histogram-gradient-boosting baselines. `src/lstm.py` trains a separate LSTM over 48-hour station windows for 24- and 48-hour targets. `src/prophet_model.py` fits per-station Prophet models. `src/evaluate.py` and `src/compare.py` calculate and combine evaluation outputs.

The notebooks provide the feature-building and baseline workflows. The shared Colab setup cells use Google Drive and `google.colab`; those setup cells are Colab-specific. The standalone LSTM and Prophet modules can be run locally after their processed inputs exist.

## Project structure

```text
app/
  SeasonalHealthDashboard/       Standalone Streamlit analytics app and its CSV
  internship_app/
    backend/
      app.py                     Flask routes and application
      services/                  AQI, OpenAQ, weather, marine, geography, and analytics services
      models/                    LSTM checkpoint and model metadata
      train_lstm.py              Model training/artifact-generation script
    static/                      CSS, JavaScript, and 227 image frames
    templates/                   Flask-rendered pages
    tests/                       Flask service and seasonal-analytics tests
    run_app.py                   Starts Streamlit and Flask
    requirements.txt             Flask application dependencies
    .env.example                 Environment-variable template
data/
  station_hour_merged.parquet    Station-hour historical dataset
  KL007_sample.csv               Small station-hour sample
src/                             Feature engineering, forecasting, and evaluation modules
notebooks/                       EDA, feature engineering, and model experiment notebooks
tests/                           Leakage tests for forecasting splits/windows
test/                            Baseline model tests
docs/TASK_CARDS.md               Project task cards
requirements.txt                 Research/notebook dependencies
```

## Technology stack

- Python 3.10 or later (the code uses Python 3.10 type syntax)
- Flask, Streamlit
- pandas, NumPy, PyArrow
- scikit-learn, PyTorch, Prophet
- Plotly; browser UI also loads Leaflet, GSAP, and Plotly from external CDNs
- OpenAQ v3, Open-Meteo Weather, and Open-Meteo Marine APIs

## Installation

Create and activate a virtual environment from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows, activate with `.venv\Scripts\activate`.

To install dependencies for both web apps:

```bash
python -m pip install -r app/internship_app/requirements.txt -r app/SeasonalHealthDashboard/requirements.txt
```

For the research/notebook pipeline, install its dependencies as well:

```bash
python -m pip install -r requirements.txt
```

The root requirements include PyTorch and Prophet. The web-app requirements alone do not install Streamlit; install the Seasonal Dashboard requirements when using the combined launcher.

## Environment configuration

The web app reads its optional `.env` file from `app/internship_app/.env`. The OpenAQ service loads `OPENAQ_API_KEY` from that file when initialized. The following variables are read by current code:

| Variable | Purpose | Default |
|---|---|---|
| `OPENAQ_API_KEY` | Enables OpenAQ v3 API requests for live station metadata and measurements. | Empty; built-in reference data/fallbacks are used. |
| `PORT` | Flask server port. | `5000` |
| `SEASONAL_STREAMLIT_PORT` | Streamlit child-process port when using `run_app.py`. | `8501` |
| `SEASONAL_STREAMLIT_URL` | URL embedded by `/seasonal-insights`; the launcher sets it from the Streamlit port. | `http://127.0.0.1:8501` |
| `AQI_HISTORY_PATH` | Station-hour Parquet file used by `/api/analytics/seasonal`. Relative paths resolve from the repository root. | `data/station_hour_merged.parquet` |
| `AQI_DATA_DIR` | Root data folder for the `src.data_loader` pipeline; it must contain the expected `processed/` files. | `data/` |

`app/internship_app/.env.example` also lists model paths, provider URLs, `FLASK_ENV`, and `DEBUG`. Those entries are not read by the current implementation: service URLs and model paths are hard-coded, and `scaler.joblib` is required at the fixed path `app/internship_app/backend/models/scaler.joblib`.

## Run the applications

### Flask web app and embedded Streamlit dashboard

From the repository root:

```bash
cd app/internship_app
python run_app.py
```

Open `http://127.0.0.1:5000`. The launcher starts Streamlit on `http://127.0.0.1:8501`; `/seasonal-insights` embeds that dashboard. `run_app.py` suppresses the child process's standard output and error streams.

### Seasonal Health Dashboard by itself

From the repository root:

```bash
python -m streamlit run app/SeasonalHealthDashboard/app.py
```

The app loads `app/SeasonalHealthDashboard/final_merged_respiratory_satellite_data.csv` by default. A CSV can also be uploaded in the sidebar; required columns are checked in the app.

### Research pipeline

The feature and baseline notebooks are designed around Colab/Drive setup. In Colab, run `notebooks/features.ipynb` to create `processed/features_v1.parquet`, then run `notebooks/anand/baselines.ipynb` to create baseline predictions and metrics.

For local module execution, make sure the required inputs are available under `<AQI_DATA_DIR>/processed/` (or under `data/processed/` when `AQI_DATA_DIR` is unset):

- `station_hour_merged.parquet` for feature-building input
- `features_v1.parquet` for model training and evaluation

`src.data_loader` expects those files inside `processed/`. The repository's station-hour dataset is at `data/station_hour_merged.parquet`, so it must be placed at the expected processed path (or the data directory configured accordingly) before running those stages.

After `features_v1.parquet` exists, run standalone model modules from the repository root:

```bash
python -m src.lstm
python -m src.prophet_model
```

They write `predictions_lstm.parquet` and `predictions_prophet.parquet` into the configured `processed/` directory. `python -m src.compare` additionally requires baseline `predictions_v1.csv` and both model prediction Parquet files. Baseline training is exposed through the notebook and `src.baselines.run_baselines()` rather than a standalone `src.baselines` command.

`app/internship_app/backend/train_lstm.py` is a separate app-model training script, not part of this research pipeline. It expects the station-hour dataset plus `scaler.joblib` and `aqi_model.joblib` in the app model directory. The latter two files are not included in this checkout; model training is therefore not reproducible from the checked-in artifacts alone.

## Flask API

All API routes are defined in `app/internship_app/backend/app.py`. Successful responses generally use a JSON object with `status: "success"` and `data`; some endpoints use endpoint-specific fields. The browser application calls the station overview, model metadata, AQI prediction, and timeline routes.

| Method and route | Purpose |
|---|---|
| `GET /api/regions/countries` | Country list. |
| `GET /api/regions/stations?page=1&limit=1000` | Global OpenAQ stations. |
| `GET /api/regions/<country_code>/states` | States/localities. |
| `GET /api/regions/<country_code>/stations?page=1&limit=1000&state=` | Country stations, optionally filtered by locality. |
| `GET /api/regions/<country_code>/cities` | Built-in reference cities. |
| `GET /api/regions/search?q=` | Geography search. |
| `GET /api/air-quality/live-status` | Whether an OpenAQ key is configured. |
| `GET /api/air-quality/current?lat=&lon=&station_id=&refresh=1` | Current station observations; `refresh=1` bypasses the cache. |
| `GET /api/air-quality/history?lat=&lon=&station_id=&hours=24` | Station history endpoint. |
| `GET /api/weather/current?lat=&lon=` | Current weather request. |
| `GET /api/weather/forecast?lat=&lon=&hours=72` | Hourly weather forecast, capped at 72 hours. |
| `POST /api/aqi/predict` | ML prediction for supplied measurements. |
| `GET /api/aqi/timeline-forecast?lat=&lon=&station_id=&hours=72` | Model forecast timeline using weather and estimated pollutant inputs. |
| `GET /api/model/metadata` | Model metadata. |
| `GET /api/station/overview?lat=&lon=&station_id=` | Combined station, weather, prediction, advisory, and optional marine response. |
| `GET /api/health/advisory?aqi=&dominant_pollutant=&temp_c=` | AQI health guidance. |
| `GET /api/marine/current?lat=&lon=` | Marine conditions and indicators. |
| `GET /api/marine/history?lat=&lon=&days=7` | Generated marine history response. |
| `GET /api/analytics/seasonal?city=&year=` | Historical city/season summary from the station-hour Parquet file. |

Example request (requires the model checkpoint **and** scaler):

```bash
curl -X POST http://127.0.0.1:5000/api/aqi/predict \
  -H 'Content-Type: application/json' \
  -d '{
    "pm25": 16.2, "pm10": 28.0, "no2": 18.0, "co": 0.4,
    "so2": 4.0, "o3": 42.0, "temperature_c": 24.0,
    "relative_humidity_pct": 55.0, "wind_speed_kmh": 10.0,
    "hour": 14, "day_of_week": 2, "month": 6, "day_of_year": 160
  }'
```

## Data and model behavior

### Data

- `data/station_hour_merged.parquet` contains historical station-hour AQI, pollutant, and weather columns. The file is used by historical analytics when no `AQI_HISTORY_PATH` is set.
- `data/KL007_sample.csv` is a sample station-hour dataset.
- `app/SeasonalHealthDashboard/final_merged_respiratory_satellite_data.csv` is the independent Streamlit dashboard's bundled dataset. It contains seasonal/monthly pollutant, weather, and pathogen fields; it is not the Flask model's training set.
- The research pipeline's processed inputs and outputs are expected under `data/processed/` or the corresponding `AQI_DATA_DIR/processed/`.

### Flask LSTM

The app inference service uses 13 ordered features: six pollutant measurements, temperature, humidity, wind speed, and four calendar fields. It scales one feature vector and repeats it across the checkpoint's 24 sequence positions before calling the PyTorch LSTM. Thus the current inference path does not construct a sequence from 24 distinct observed hours.

The service also computes deterministic pollutant sub-indices and a category alongside the model prediction. The timeline route adjusts current pollutant values with simple empirical factors and pairs them with weather forecast inputs; it is not a direct observation of future pollutant concentrations.

The checkpoint metadata reports MAE `17.641586`, RMSE `33.714321`, and R² `0.661795`. These values are metadata claims, not independently reproduced results. The metadata reports 12,000 training and test samples, while `backend/train_lstm.py` currently sets limits of up to 40,000 training rows and 10,000 test rows; treat the recorded provenance/metrics as needing verification.

### Research forecasting models

The research pipeline targets AQI 24 and 48 hours ahead, using station-level time-based train/gap/test splits and leakage-aware windows. It includes persistence, linear regression, histogram gradient boosting (with quantile prediction bounds), an independently trained LSTM, and per-station Prophet models. The source code and notebooks define the transformations and metrics; outputs must be generated from the required input files before comparison.

### Provenance and fallbacks

- OpenAQ measurements are live only when the API returns usable recent observations. Missing/stale pollutant values can be filled from defaults; a response can therefore contain both observations and estimates.
- Without an OpenAQ key, the app uses built-in reference geography and fallback pollutant values. These are not live readings.
- `/api/air-quality/history` prefers matching station-hour rows from `data/station_hour_merged.parquet`; if no usable rows are found, it returns an estimated diurnal curve, not verified historical observations. This route uses that fixed repository path and does not use `AQI_HISTORY_PATH`.
- Weather and marine API requests can return hard-coded fallback values when unavailable. The weather forecast service can return a synthetic timeline.
- Marine physical fields are requested from Open-Meteo Marine. Several biogeochemical fields in the current marine service are calculated from latitude-based formulas rather than fetched as direct Copernicus observations. The marine history endpoint constructs a timeline from current values, not a verified historical archive.
- Seasonal analytics are aggregations of historical station-hour records, not model forecasts. The standalone Streamlit app computes descriptive statistics/correlations from its bundled CSV.

## Tests

Run the test groups from the repository root:

```bash
python -m unittest discover -s test -p 'test_*.py' -v
python -m unittest discover -s tests -v
python -m unittest discover -s app/internship_app/tests -p 'test_*.py' -v
```

The tests cover baseline output/evaluation, forecasting-window leakage, selected Flask/OpenAQ routes, and historical seasonal analytics. The Prophet-dependent leakage test requires the root `requirements.txt` dependencies.

## Troubleshooting and limitations

- **Prediction routes return an artifact error:** `app/internship_app/backend/models/scaler.joblib` is required but absent from this checkout. `aqi_lstm.pt` alone is not sufficient. The metadata route also triggers artifact loading.
- **App model training cannot start:** the training script also expects `aqi_model.joblib` and the scaler. Neither is included. Do not retrain unless those inputs and their provenance are available.
- **Seasonal analytics reports missing history:** provide the Parquet path through `AQI_HISTORY_PATH`. It must contain `City`, `StationId`, `Datetime`, `AQI`, six pollutant fields, and three weather fields.
- **Research pipeline reports missing processed files:** place inputs under `<AQI_DATA_DIR>/processed/` using the expected filenames. The root dataset currently resides at `data/station_hour_merged.parquet`, while the research loader expects it under `processed/`.
- **Live station data is unavailable:** configure `OPENAQ_API_KEY` in `app/internship_app/.env` and check network/API availability. Fallback/reference values are not live observations.
- **Seasonal dashboard does not start from the combined launcher:** ensure `app/SeasonalHealthDashboard/requirements.txt` is installed; the Flask-only requirements do not include Streamlit.
- **External visual components do not load:** the browser UI fetches map/chart/animation libraries and map tiles from external services, so network access is required for those third-party assets.

The Flask AQI model cannot currently perform inference from the checked-in model files alone because its scaler is missing. OpenAQ access and some data files are optional for application startup but affect which features can return live or historical results. The application is an informational software project, not a substitute for official monitoring or medical advice.

## License

See [LICENSE](LICENSE).
