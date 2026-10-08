# AQI-Air-_pollution_prediction

# Real-Time Air Quality Forecasting & Public Health Advisory Engine

A machine learning project for forecasting **Air Quality Index (AQI)** and generating health advisories based on predicted air pollution levels.

The project combines historical air-quality measurements with weather information to identify pollution patterns and predict future AQI levels. The initial prototype focuses on **Tokyo, Japan** and is designed to eventually provide real-time forecasts and public health recommendations.

---

## 📌 Project Overview

Air pollution can change significantly over short periods of time. Being able to predict upcoming pollution levels can help people take preventive measures before air quality becomes unhealthy.

This project aims to build an end-to-end pipeline that:

- Collects historical air-quality data
- Collects historical weather data
- Cleans and preprocesses the data
- Calculates AQI using pollutant concentrations
- Performs exploratory data analysis
- Creates time-series features
- Trains machine learning models to forecast future AQI
- Generates health advisories based on predicted AQI
- Provides an interactive Streamlit dashboard

---

## 🎯 Objectives

1. Collect air-quality data from OpenAQ.
2. Collect historical weather data from Open-Meteo.
3. Synchronize pollution and weather data by timestamp.
4. Calculate AQI from pollutant concentrations.
5. Analyze pollution trends and seasonal patterns.
6. Create time-series features such as lag values and rolling averages.
7. Train baseline machine learning models for AQI forecasting.
8. Compare forecasting models.
9. Generate health advisories from predicted AQI levels.
10. Build an interactive dashboard for displaying AQI forecasts.

---

## 🗂️ Project Structure

```text
AQI-Air-_pollution_prediction-1/
│
├── data/
│   ├── raw/
│   │   ├── openaq/
│   │   └── openmeteo/
│   │
│   └── processed/
│
├── notebooks/
│   └── 01_data_collection.ipynb
│
├── src/
│
├── .env
├── .gitignore
├── LICENSE
├── requirements.txt
└── README.md
```

### Directory Description

| Directory/File     | Purpose                                            |
| ------------------ | -------------------------------------------------- |
| `data/raw/`        | Stores downloaded raw datasets                     |
| `data/processed/`  | Stores cleaned and processed datasets              |
| `notebooks/`       | Collab notebooks for experimentation and analysis |
| `src/`             | Python source code for the project                 |
| `.env`             | Stores API keys and environment variables          |
| `.gitignore`       | Specifies files Git should not track               |
| `requirements.txt` | Lists required Python packages                     |
| `LICENSE`          | Project license                                    |
| `README.md`        | Project documentation                              |

---

## 📊 Data Sources

### OpenAQ

OpenAQ is used as the primary source for air-quality measurements.

The project uses pollutant measurements such as:

- PM2.5
- PM10
- NO₂
- O₃
- SO₂

### Open-Meteo

Open-Meteo is used to obtain historical weather information such as:

- Temperature
- Relative humidity
- Wind speed
- Wind direction
- Atmospheric pressure

---

## 🧠 Machine Learning Approach

The project uses a time-series forecasting approach.

### Feature Engineering

Historical pollution and weather data are transformed into features such as:

- 1-hour lag
- 6-hour lag
- 12-hour lag
- 24-hour lag
- 6-hour rolling average
- 12-hour rolling average
- 24-hour rolling average
- Hour of day
- Day of week
- Month

These features help the model learn relationships between recent pollution levels, weather conditions, and future AQI.

### Models

The initial baseline models include:

- Linear Regression
- Random Forest

An advanced forecasting model will be evaluated later, such as:

- LSTM
- Prophet

---

## 🌡️ AQI Calculation

AQI is calculated from pollutant concentrations using pollutant-specific breakpoint ranges.

The overall AQI is determined from the pollutant sub-indices, with the highest relevant pollutant sub-index determining the overall AQI.

Weather variables are **not directly used to calculate AQI**. Instead, weather information is used as an input feature for the machine learning forecasting model.

---

## 🚨 Health Advisory System

The predicted AQI is mapped to corresponding health-risk categories.

The system will generate recommendations based on the predicted air-quality level, such as guidance for:

- General population
- Sensitive groups
- Outdoor activities
- Exposure reduction

---

## 🖥️ Planned Dashboard

The project will use **Streamlit** to create an interactive dashboard containing:

- Current AQI
- Predicted AQI
- AQI forecast
- Historical AQI trends
- Pollutant breakdown
- Weather information
- Health advisory
- Interactive visualizations

---

## 🛠️ Technologies

- **Python**
- **Pandas**
- **NumPy**
- **Scikit-learn**
- **Matplotlib**
- **Seaborn**
- **Plotly**
- **Streamlit**
- **Folium**
- **OpenAQ API**
- **Open-Meteo API**
- **Jupyter Notebook**

Advanced modelling may additionally use **PyTorch/LSTM** or **Prophet**.

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/GOKUL5287/AQI-Air-_pollution_prediction.git
cd AQI-Air-_pollution_prediction
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

Activate it:

#### macOS / Linux

```bash
source .venv/bin/activate
```

#### Windows

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```text
OPENAQ_API_KEY=your_api_key_here
```

Do **not** commit the `.env` file to GitHub.

The `.env` file is excluded through `.gitignore`.

---

## 🚀 Project Status

### Current Progress

- [ ] GitHub repository created
- [ ] Project structure created
- [ ] `requirements.txt` created
- [ ] `.gitignore` configured
- [ ] MIT License added
- [ ] OpenAQ data collection
- [ ] Open-Meteo data collection
- [ ] Data cleaning
- [ ] AQI calculation
- [ ] Exploratory data analysis
- [ ] Feature engineering
- [ ] Baseline ML models
- [ ] Advanced forecasting model
- [ ] Health advisory engine
- [ ] Streamlit dashboard

---

## 📈 Future Improvements

Future versions of the project may include:

- Multiple Tokyo monitoring stations
- Multiple-city forecasting
- Real-time AQI updates
- Improved forecasting models
- Confidence intervals for predictions
- Interactive maps
- Automated health alerts
- More detailed pollutant analysis

---

## 📄 License

This project is licensed under the **MIT License**.

See the [`LICENSE`](LICENSE) file for details.

---

## 👤 Author

**Gokul V S**

GitHub: [GOKUL5287](https://github.com/GOKUL5287)
