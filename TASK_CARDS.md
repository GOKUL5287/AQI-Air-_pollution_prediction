# AQI Forecasting Project: Week 1 Fix and Week 2 Task Cards

Team of six · Final deadline Fri 30 Oct 2026 · Week 2 exit Fri 16 Oct 2026 · Prepared Wed 14 Oct 2026

## Read this first (5 minutes)

**What happened.** We started without an agreed final product or agreed handoff files, so the DSA side and the AI/ML side each built their own weather file, merged table, train/test split and model. Both were honest attempts, but they do not fit together. This sheet fixes that by giving every file one owner and one fixed set of columns.

**The one flow.** Three shared files, each with one owner:

1. **D1** `station_hour_merged.parquet`: one row per station per hour, with pollutants, AQI and weather. Owner: Kanchana.
2. **D2** `features_v1.parquet`: past-only features, the two targets and a train/gap/test label. Owner: Gokul.
3. **D3** `predictions_v1.csv` and `metrics_v1.csv`: predictions and scores for persistence, Linear Regression and gradient boosting. Owner: Anand.

The DSA team reads D1 and produces the history, calendar, pollutant-breakdown and weather-insight outputs. They own those four panels of the final app. AI/ML owns the forecast and advisory panels. The map and the downloadable report are joint.

**Five rules.**

1. Notebooks are private. Work in `notebooks/<your name>/` and never edit someone else's notebook.
2. Only two things are shared: `.py` files in `src/` on GitHub, and data files in the shared Drive folder with the exact columns below.
3. Nobody pushes to `main`. Use a branch named `<name>/<task>`, open a pull request, and the named reviewer approves it.
4. Column names in this sheet are fixed. To change one, tell the owner and the next person downstream first.
5. If your input is not ready, build against the one-station sample (station KL007) using the agreed columns. Nobody waits.

**Words you will hear.**

- **Target:** the number the model must predict, here the hourly AQI 24 and 48 hours after the row's time.
- **Lag:** an earlier value, for example the AQI 24 hours before.
- **Leakage:** a feature that secretly contains information from the future. It makes scores look great and be fake.
- **Chronological split:** train on the past, test on the future, never shuffle.
- **Persistence baseline:** predict that tomorrow's AQI equals today's. A model only counts if it beats this.

## Fixed definitions (everyone)

- Row key: `StationId` + `Datetime`. Datetime is hourly, India time, with no timezone attached.
- AQI means the Kaggle `AQI` column. There is no `AQI_final`: no missing AQI could be recovered, so it would be identical.
- Targets: `Target_AQI_24h` and `Target_AQI_48h` are the AQI at the same station exactly 24 and 48 hours later.
- Test period: the last 20% of timestamps, with a 48-hour gap before it. Everything from 25 Mar 2020 (the national lockdown) is flagged separately, because lockdown air quality is not typical.

## Card 1: Kanchana, build D1

**Goal:** one merged table that every other task reads.

**Input:** raw `station_hour.csv` and `stations.csv`, plus the weather file from the 03 notebook.

**Do:**
1. In the 03 notebook add `wind_direction_10m` to the hourly list and save it as column `Wind_Direction_deg`. Keep `timezone=Asia/Kolkata`. Re-run and save `openmeteo_india_weather.csv` to `data/raw/`.
2. Merge stations onto station_hour by `StationId`, then weather by `City` + `Datetime`. Use `validate='many_to_one'` on both merges.
3. Sort by `StationId`, `Datetime` and save as parquet in `data/processed/`. Also save a small CSV of station KL007 for everyone to build against today.

**Output columns (24, in this order):** StationId, StationName, City, State, Status, Datetime, PM2.5, PM10, NO, NO2, NOx, NH3, CO, SO2, O3, Benzene, Toluene, Xylene, AQI, AQI_Bucket, Temperature_C, Relative_Humidity_pct, Wind_Speed_kmh, Wind_Direction_deg

**Done when:**
- Row count is exactly 2,589,083, the same as raw `station_hour`. The merge must not add or drop rows.
- No duplicate (`StationId`, `Datetime`) pairs.
- Missing percentage printed for every weather column.
- `Datetime` is a real datetime type.

**Reviewer:** Gokul. **Due:** Thu 15 Oct, 10:00.

## Card 2: Gokul, build D2

**Goal:** the model-ready table, with no leakage and one official train/test split.

**Input:** D1.

**Rules:** compute everything per station on the full sorted table, before any row is dropped. A feature may only use information from `Datetime` or earlier. Put the code in `src/features.py` and `src/split.py`.

**Output columns:**
- Keys: StationId, City, Datetime
- Targets: Target_AQI_24h, Target_AQI_48h
- Labels: split (train, gap or test), is_lockdown (true from 25 Mar 2020)
- Current values: AQI, PM2.5, PM10, NO2, NOx, NH3, CO, SO2, O3
- Weather: Temperature_C, Relative_Humidity_pct, Wind_Speed_kmh, Wind_Dir_sin, Wind_Dir_cos (wind direction is circular, so it must be sin and cos, never raw degrees)
- Calendar: Hour_sin, Hour_cos, DayOfWeek_sin, DayOfWeek_cos, Month_sin, Month_cos, DayOfYear
- Lags: AQI_lag_1h, AQI_lag_6h, AQI_lag_12h, AQI_lag_24h, AQI_lag_48h
- Rolling: AQI_rolling_mean_6h, AQI_rolling_mean_12h, AQI_rolling_mean_24h (need at least half the window present)

**Rows kept:** every row where `AQI` is not missing. Targets and lags may be missing, and each model drops the rows missing its own target. Persistence needs the current AQI, which is why rows are kept this way.

**Split rule:** `test_start` is the 80th percentile of unique timestamps. The gap is the 48 hours before it, the test set is `test_start` onward, and train is everything before the gap.

**Done when:**
- Code asserts there are no missing hourly timestamps inside each station's range.
- A leakage test passes: for 1,000 random rows, `AQI_lag_24h` equals the AQI looked up at `Datetime` minus 24 hours.
- Row counts and date ranges are printed for each split.

**Reviewer:** Kanchana. **Due:** Thu 15 Oct, 14:00. Start today on the KL007 sample.

## Card 3: Anand, repo first, then baselines

**Part A, today by 18:00: repo and loader.**
1. Create the structure: `src/`, `notebooks/<name>/`, `docs/`, `reports/`, `data/reference/`, `README.md` with the run order, `requirements.txt`, and a `.gitignore` that excludes `data/raw`, `data/processed`, `*.parquet` and `.ipynb_checkpoints`.
2. Turn on branch protection for `main` (GitHub Settings, then Branches): pull request required.
3. Push `data_loader.py` and `aqi_functions.py` into `src/`.
4. In `data_loader.py`, make the data folder configurable: `DATA_DIR = Path(os.environ.get('AQI_DATA_DIR', <repo>/data))`. Every Colab notebook's first cell mounts Drive, sets `AQI_DATA_DIR` to the shared Drive data folder, and clones or pulls the repo.
5. Add `load_merged()`, `load_features()` and `load_dominant()` pointing at the file names in this sheet. Delete `load_aqi_calculated()`, because that file is never produced.
6. Add a notebook template with that first cell, so nobody sets paths by hand.

**Part B, Thu evening to Fri: baselines.** Put the code in `src/baselines.py` and `src/evaluate.py`. For each horizon (24 and 48): train on `split == 'train'`, test on `split == 'test'`, dropping rows missing that horizon's target. Three models:
- Persistence: prediction equals the current `AQI`.
- Linear Regression, with a median imputer fitted on the training rows only.
- HistGradientBoostingRegressor, which handles missing values, so no imputation.

Features are every D2 column except keys, targets, `split` and `is_lockdown`.

**Output D3:**
- `predictions_v1.csv`: StationId, Datetime, horizon_h, model, y_true, y_pred
- `metrics_v1.csv`: model, horizon_h, subset (test_all or test_excl_lockdown), n_rows, MAE, RMSE

**Stretch (Fri):** gradient boosting with quantile loss at 5% and 95%. Add `pi_lo` and `pi_hi` columns to the predictions and a coverage figure to the metrics.

**Done when:** persistence appears for both horizons, the notebook runs top to bottom, and one sentence says whether gradient boosting beats persistence.

**Reviewer:** Kanchana. **Due:** repo Wed 18:00, baselines Fri 12:00.

## Card 4: Aravind, coverage and data dictionary

**Goal:** tell the team which stations have enough data to forecast and show.

**Input:** D1.

**Output 1:** `data/reference/station_coverage.csv` with columns StationId, StationName, City, State, first_datetime, last_datetime, n_rows, aqi_rows, aqi_pct, pollutants_measured (how many of the 7 AQI pollutants ever appear), longest_aqi_gap_hours, usable_for_forecast.

Proposed rule for `usable_for_forecast`: at least 8,760 AQI hours (one year) and `aqi_pct` of at least 60. The team confirms or changes this on Thursday.

**Output 2:** `docs/DATA_DICTIONARY.md`: every D1 column with meaning, unit (pollutants are in ug/m3 except NOx in ppb and CO in mg/m3) and percent missing.

**Output 3:** `data/reference/city_coordinates.csv` with columns City, Latitude, Longitude. Copy the 26 cities from the weather notebook. The final map will be city-level, because `stations.csv` has no coordinates. Station-level markers are optional if time remains.

**Also:** spend at most one hour looking on data.gov.in for hospital or respiratory data. Write a three-line note saying what you found or that nothing suitable exists.

**Reviewer:** Vrinda. **Due:** coverage Thu 12:00, the rest Fri 12:00.

## Card 5: Vrinda, patterns and calendar

**Goal:** the historical analysis and the calendar heatmap for the app.

**Input:** D1, and Aravind's `usable_for_forecast` flag when it arrives.

**Build:**
1. `src/aggregate.py` with `to_daily(df)`. It returns StationId, City, Date, AQI_mean (mean of that day's hourly AQI), AQI_max and n_hours, and sets AQI_mean to missing when n_hours is under 16.
2. `src/viz.py` with `calendar_heatmap(daily, station_id, year)`, returning a Plotly figure coloured by the CPCB categories: 0 to 50 Good, 51 to 100 Satisfactory, 101 to 200 Moderate, 201 to 300 Poor, 301 to 400 Very Poor, above 400 Severe.
3. The analysis: month by city AQI, weekday against weekend, hour-of-day profile, and a city comparison for usable stations.

**Output:** `docs/EDA_FINDINGS.md` with 5 to 8 findings. Each has one chart (saved in `reports/figures/`), the date coverage, the units, and one sentence of interpretation the chart supports. Mark the 2020 lockdown period on the charts instead of hiding it.

**Reviewer:** Aiswarya. **Due:** `to_daily` and the calendar Thu evening, findings Fri 12:00.

## Card 6: Aiswarya, dominant pollutant and weather

**Goal:** show which pollutant drives the AQI, and how weather relates to PM2.5.

**Input:** D1 and `src/aqi_functions.py`.

**Build `src/aqi_dominant.py`:**
- Per station, sorted by time: 24-row rolling mean (at least 16 values) for PM2.5, PM10, SO2, NOx and NH3, and 8-row rolling maximum (at least 1 value) for CO and O3. Use these same rules so the check below passes. Note in the docs that this follows the dataset's method.
- Apply the sub-index functions to non-missing values only. The functions return 0 for a missing value, which would be wrong.
- For speed, do not apply row by row. Compute the sub-index once per unique value and map the results back.

**Output D4:** `data/processed/dominant_pollutant.parquet` with columns StationId, Datetime, PM2.5_SI, PM10_SI, SO2_SI, NOx_SI, NH3_SI, CO_SI, O3_SI, Dominant_Pollutant (the pollutant with the highest sub-index, missing if all are missing).

**Check:** where both exist, the rounded maximum sub-index should equal the dataset's `AQI` on about 99.9% of rows, as in the 02 notebook. Print the match percentage and the number of mismatches.

**Weather analysis:** write `docs/WEATHER_ASSOCIATION.md`.
- Use Spearman correlation, because the data is skewed: PM2.5 against temperature, humidity and wind speed, per city.
- Group wind direction into 8 compass sectors and show median PM2.5 per sector, for cities with at least a year of PM2.5.
- State clearly that the weather values are grid estimates for the city centre, not measurements at the sensor, so the links are approximate.

**Reviewer:** Aravind. **Due:** module Thu evening, document Fri 12:00.

## Day plan

**Wed 14 Oct:** team call. Anand finishes the repo and loader by 18:00. Kanchana starts D1. Gokul and the DSA members start on the KL007 sample.

**Thu 15 Oct:** D1 in Drive by 10:00, then Gokul's D2 by 14:00, then Anand's first baseline run in the evening. Aravind's coverage table by 12:00. Vrinda's and Aiswarya's modules by evening.

**Fri 16 Oct:** everything final by 12:00. Then a 20-minute demo, 3 minutes each: show your output file, its columns, and one thing you learned or one limitation.

**After Friday:** Streamlit app Oct 19 to 23, evaluation write-up, README and demo Oct 26 to 30.

## Not in Week 2

LSTM and Prophet wait until the baselines show whether they are worth trying. Health correlation depends on whether Aravind finds data. OpenAQ is a stretch goal for after the app works.
