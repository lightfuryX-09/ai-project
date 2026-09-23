# data generator for weather data 
import requests
import pandas as pd
from datetime import date, timedelta, datetime 


def get_city_coordinates(city: str) -> tuple[float, float]:
    """Use Open-Meteo geocoding to find latitude and longitude for a city."""
    geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 1, "language": "en", "format": "json"}
    response = requests.get(geocode_url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json().get("results")
    if not data:
        raise ValueError(f"Could not find coordinates for city: {city}")
    location = data[0]
    return float(location["latitude"]), float(location["longitude"])


def fetch_historical_weather(city: str, years: int = 5, output_csv: str = "historical_weather.csv") -> pd.DataFrame:
    """Fetch at least the last `years` of daily historical weather and save date + temperature to CSV."""
    lat, lon = get_city_coordinates(city)
    end_date = date.today() 
    start_date = end_date - timedelta(days=years * 365.25)
    weather_url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": ",".join(["temperature_2m_mean", "relative_humidity_2m_mean", "wind_speed_10m_max", "precipitation_sum", "weathercode", "sunrise", "sunset"]),    
        "timezone": "auto",
        }    
    response = requests.get(weather_url, params=params, timeout=30)
    response.raise_for_status()
    print("status code:", response.status_code)
    print("response text:", response.text[:500])  # Print first 500 characters of the response for debugging
    payload = response.json()
    daily = payload.get("daily", {})
    dates = daily.get("time", [])
    temperatures = daily.get("temperature_2m_mean", [])
    humidity = daily.get("relative_humidity_2m_mean",[])
    windspeed = daily.get("wind_speed_10m_max",[])
    precipitation = daily.get("precipitation_sum",[])
    weathercode = daily.get("weathercode",[])
    sunrise = daily.get("sunrise",[])
    sunset = daily.get("sunset",[])
    if not dates or not temperatures or len(dates) != len(temperatures):
        raise ValueError("Invalid weather data returned from API.")
        print("Dates:", len(dates))
        print("Temperatures:", len(temperatures))
        print("Humidity:", len(humidity))
        print("Windspeed:", len(windspeed))
        print("Precipitation:", len(precipitation))
        print("Weathercode:", len(weathercode))
        print("Sunrise:", len(sunrise))
        print("Sunset:", len(sunset))
    df = pd.DataFrame({"date": dates, "temperature": temperatures, "humidity": humidity, "windspeed": windspeed, "precipitation": precipitation,
                       "weathercode": weathercode, "sunrise": sunrise, "sunset": sunset})
    
    df['sunrise'] = pd.to_datetime(df['sunrise']).dt.strftime('%H:%M')
    df['sunset'] = pd.to_datetime(df['sunset']).dt.strftime('%H:%M')
    df.to_csv(output_csv, index=False)
    return df 

# learning model for weather prediction 
import sklearn
from sklearn.linear_model import LinearRegression
import numpy as np
import sys 

def load_city_csv(city: str, folder: str = ".") -> pd.DataFrame:
    """Load the historical weather CSV for a given city."""
    filename = f"city_historical_weather.csv"
    try:
        df = pd.read_csv(filename)
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV for city '{city}' not found at {filename}")
    return df

def prepare_features(df: pd.DataFrame, lags: int = 7) -> tuple[np.ndarray, np.ndarray, pd.Index]:
    """Prepare lagged features for temperature Prediction"""
    if 'temperature' not in df.columns:
        raise ValueError("CSV must contain a 'temperature' column")
    data = df[['temperature']].copy()
    for i in range(1, lags +1):
        data [f'lag_{i}'] = data['temperature'].shift(i)
    data = data.dropna()
    x = data[[f'lag_{i}' for i in range(1, lags + 1)]].values
    y = data['temperature'].values
    return x,y, data.index
    
def train_model(x: np.ndarray, y: np.ndarray) -> LinearRegression:
    """Train a linera regression model on the lagged features."""
    model = LinearRegression()
    model.fit(x,y)
    return model

def predict_next_days(model: LinearRegression, recent_temps: np.ndarray, days: int = 7) -> list[float]:
    """Predict the next days of temperature based on the most recent observed temperature."""
    lags = len(recent_temps)
    preds = []
    window = list(recent_temps)
    for _ in range(days) :
        x = np.array(window[:lags]).reshape(1, -1)
        p = float(model.predict(x)[0])
        preds.append(p)
        window = [p] + window[:lags -1]
    
    
    return preds
        
def predict_city_next_week(city: str, folder: str = ".") -> pd.DataFrame:
    """Predict the next 7 days of temperature for a given city."""
    df = load_city_csv(city, folder)
    df['date'] = pd.to_datetime(df['date'])
    x, y, idx = prepare_features(df, lags=7)
    model = train_model(x,y)
    temps = df['temperature'].dropna().values
    if len(temps) < 7:
        raise ValueError(f"Not enough temperature data to predict for city '(city)'. Need at least 7 days of data.")
    recent = temps[::-1][:7]
    preds = predict_next_days(model, recent, days=7)
    future_dates = [df['date'].max() + pd.Timedelta(days=i) for i in range(1, 8)]
    result = pd.DataFrame({'date': future_dates, 'predicted temperature': preds})
    return result 

if __name__ == "__main__":
    city = input("Enter city name: ")
    df = fetch_historical_weather(city, years=5, output_csv=f"city_historical_weather.csv")
    try:
        predictions = predict_city_next_week(city)
        print(predictions)
    except Exception as e:
        print(f"Error predicting temperature for city '{city}': {e}")
        sys.exit()

        print(f"Predicted temperatures for the next 7 days in {city}:")
        print(predictions)
row = df.iloc[-1]

print(f"\n most recent weather data for {city}:")
print(f"Date: {row['date']}")
print(f"Temperature: {row['temperature']}")
print(f"Humidity: {row['humidity']}")
print(f"Windspeed: {row['windspeed']}")
print(f"Precipitation: {row['precipitation']}")
print(f"Weathercode: {row['weathercode']}")
print(f"Sunrise: {row['sunrise']}")
print(f"Sunset: {row['sunset']}")