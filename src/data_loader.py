'''
This module loads the Original Kaggle AQI data using pandas and pathlib.
'''


import pandas as pd
from pathlib import Path


DATA_RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
DATA_PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"


def load_station_hour():
    file_path = DATA_RAW / "station_hour.csv"
    return pd.read_csv(file_path)


def load_station_day():
    file_path = DATA_RAW / "station_day.csv"
    return pd.read_csv(file_path)


def load_city_hour():
    file_path = DATA_RAW / "city_hour.csv"
    return pd.read_csv(file_path)


def load_city_day():
    file_path = DATA_RAW / "city_day.csv"
    return pd.read_csv(file_path)


def load_stations():
    file_path = DATA_RAW / "stations.csv"
    return pd.read_csv(file_path)


def load_weather():
    file_path = DATA_RAW / "openmeteo_india_weather.csv" 
    return pd.read_csv(file_path)


def load_aqi_calculated():
    file_path = DATA_PROCESSED / "aqi_calculated.csv"
    return pd.read_csv(file_path)


# if __name__ == "__main__":
#     df_station_hour = load_station_hour()
#     df_station_day = load_station_day()
#     df_city_hour = load_city_hour()
#     df_city_day = load_city_day()
#     df_stations = load_stations()
    # df_weather = load_weather()

#     print("df_station_hour:", df_station_hour.shape)
#     print("df_station_day:", df_station_day.shape)
#     print("df_city_hour:", df_city_hour.shape)
#     print("df_city_day:", df_city_day.shape)
#     print("df_stations:", df_stations.shape)
