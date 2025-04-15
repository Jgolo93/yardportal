"""
Weather Service Module
----------------------
This module handles fetching real-time weather data from AccuWeather API.
It provides functions to get current conditions and forecasts for specific locations.
"""

import requests
import json
import os
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# AccuWeather API configuration
# You need to register at https://developer.accuweather.com/ to get an API key
ACCUWEATHER_API_KEY = os.environ.get('ACCUWEATHER_API_KEY', '7PlLdEWrfBlj4HIQ5GI8xtABGWtXNpHs')
BASE_URL = "http://dataservice.accuweather.com"

# API endpoints
LOCATION_ENDPOINT = "/locations/v1/cities/search"
CURRENT_CONDITIONS_ENDPOINT = "/currentconditions/v1/"
FORECAST_ENDPOINT = "/forecasts/v1/daily/5day/"

# Cache to store weather data and reduce API calls
# Format: {location_key: {'data': {...}, 'timestamp': datetime}}
weather_cache = {}
# Cache for location keys to reduce API calls
# Format: {city_name: {'key': location_key, 'timestamp': datetime}}
location_cache = {}
# Cache expiration time (in minutes)
CACHE_EXPIRATION = 60

def get_location_key(city, country=""):
    """
    Get the AccuWeather location key for a city.

    Args:
        city (str): City name
        country (str, optional): Country name or code

    Returns:
        str: Location key or None if not found
    """
    if not ACCUWEATHER_API_KEY:
        logger.error("AccuWeather API key is not set")
        return None

    # Check if city is empty or None
    if not city:
        logger.error("City name is empty or None")
        return None

    # Normalize city name for caching (lowercase)
    cache_city = city.lower()

    logger.info(f"Looking up location key for city: {city} (cache key: {cache_city})")

    # Check cache first
    if cache_city in location_cache:
        cache_entry = location_cache[cache_city]
        if datetime.now() - cache_entry['timestamp'] < timedelta(minutes=CACHE_EXPIRATION):
            logger.info(f"Using cached location key for {city}: {cache_entry['key']}")
            return cache_entry['key']
        else:
            logger.info(f"Cached location key for {city} has expired, fetching new one")

    try:
        # Build the query parameters
        query = f"{city}"
        if country:
            query += f",{country}"

        params = {
            'apikey': ACCUWEATHER_API_KEY,
            'q': query
        }

        logger.info(f"Making AccuWeather API request for location: {query}")

        # Make the API request
        response = requests.get(f"{BASE_URL}{LOCATION_ENDPOINT}", params=params)
        response.raise_for_status()  # Raise exception for HTTP errors

        # Parse the response
        locations = response.json()

        if not locations:
            logger.warning(f"No location found for {query}")
            return None

        # Get the key of the first (most relevant) location
        location_key: object = locations[0]['Key']

        # Cache the result
        location_cache[cache_city] = {
            'key': location_key,
            'timestamp': datetime.now()
        }

        logger.info(f"Successfully retrieved location key for {city}: {location_key}")
        return location_key

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching location key: {e}")
        return None
    except (KeyError, IndexError) as e:
        logger.error(f"Error parsing location data: {e}")
        return None

def get_current_weather(location_key):
    """
    Get current weather conditions for a location.

    Args:
        location_key (str): AccuWeather location key

    Returns:
        dict: Current weather data or None if error
    """
    if not location_key:
        return None

    # Check cache first
    cache_key = f"current_{location_key}"
    if cache_key in weather_cache:
        cache_entry = weather_cache[cache_key]
        if datetime.now() - cache_entry['timestamp'] < timedelta(minutes=CACHE_EXPIRATION):
            logger.info(f"Using cached current weather for location {location_key}")
            return cache_entry['data']

    try:
        params = {'apikey': ACCUWEATHER_API_KEY}
        response = requests.get(f"{BASE_URL}{CURRENT_CONDITIONS_ENDPOINT}{location_key}", params=params)
        response.raise_for_status()

        data = response.json()
        if not data:
            return None

        # Extract relevant weather information
        current_weather = {
            'temperature': data[0]['Temperature']['Metric']['Value'],
            'temperature_unit': data[0]['Temperature']['Metric']['Unit'],
            'weather_text': data[0]['WeatherText'],
            'weather_icon': data[0]['WeatherIcon'],
            'has_precipitation': data[0]['HasPrecipitation'],
            'precipitation_type': data[0].get('PrecipitationType', None),
            'is_day_time': data[0]['IsDayTime'],
            'relative_humidity': data[0].get('RelativeHumidity', None),
            'wind_speed': data[0].get('Wind', {}).get('Speed', {}).get('Metric', {}).get('Value', 0),
            'wind_unit': data[0].get('Wind', {}).get('Speed', {}).get('Metric', {}).get('Unit', 'km/h'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Cache the result
        weather_cache[cache_key] = {
            'data': current_weather,
            'timestamp': datetime.now()
        }

        return current_weather

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching current weather: {e}")
        return None
    except (KeyError, IndexError) as e:
        logger.error(f"Error parsing weather data: {e}")
        return None

def get_forecast(location_key):
    """
    Get 5-day weather forecast for a location.

    Args:
        location_key (str): AccuWeather location key

    Returns:
        dict: Forecast data or None if error
    """
    if not location_key:
        return None

    # Check cache first
    cache_key = f"forecast_{location_key}"
    if cache_key in weather_cache:
        cache_entry = weather_cache[cache_key]
        if datetime.now() - cache_entry['timestamp'] < timedelta(minutes=CACHE_EXPIRATION):
            logger.info(f"Using cached forecast for location {location_key}")
            return cache_entry['data']

    try:
        params = {
            'apikey': ACCUWEATHER_API_KEY,
            'metric': 'true'  # Use metric units
        }
        response = requests.get(f"{BASE_URL}{FORECAST_ENDPOINT}{location_key}", params=params)
        response.raise_for_status()

        data = response.json()

        # Extract headline and daily forecasts
        forecast = {
            'headline': data['Headline']['Text'],
            'daily_forecasts': []
        }

        for daily in data['DailyForecasts']:
            day_forecast = {
                'date': daily['Date'],
                'min_temp': daily['Temperature']['Minimum']['Value'],
                'max_temp': daily['Temperature']['Maximum']['Value'],
                'day_icon': daily['Day']['Icon'],
                'day_phrase': daily['Day']['IconPhrase'],
                'day_has_precipitation': daily['Day']['HasPrecipitation'],
                'day_precipitation_type': daily['Day'].get('PrecipitationType', None),
                'day_precipitation_probability': daily['Day'].get('PrecipitationProbability', 0),
                'night_icon': daily['Night']['Icon'],
                'night_phrase': daily['Night']['IconPhrase'],
                'night_has_precipitation': daily['Night']['HasPrecipitation'],
                'night_precipitation_type': daily['Night'].get('PrecipitationType', None),
                'night_precipitation_probability': daily['Night'].get('PrecipitationProbability', 0)
            }
            forecast['daily_forecasts'].append(day_forecast)

        # Cache the result
        weather_cache[cache_key] = {
            'data': forecast,
            'timestamp': datetime.now()
        }

        return forecast

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching forecast: {e}")
        return None
    except (KeyError, IndexError) as e:
        logger.error(f"Error parsing forecast data: {e}")
        return None

def get_weather_for_date(city, date_str):
    """
    Get weather forecast for a specific date and city.

    Args:
        city (str): City name
        date_str (str): Date string in format 'YYYY-MM-DD'

    Returns:
        dict: Weather data for the specified date or None if not available
    """
    try:
        # Validate city input
        if not city or not isinstance(city, str) or city.strip() == "":
            logger.warning("Invalid city parameter provided")
            city = "Johannesburg"  # Default fallback
        else:
            city = city.strip()  # Remove any leading/trailing whitespace

        logger.info(f"Getting weather for {city} on {date_str}")

        # Get location key for the city
        location_key = get_location_key(city)
        if not location_key:
            logger.warning(f"Could not find location key for city: {city}")
            return None

        # Get 5-day forecast
        forecast = get_forecast(location_key)
        if not forecast:
            logger.warning(f"Could not get forecast for location key: {location_key}")
            return None

        # Find the forecast for the specified date
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        for daily in forecast['daily_forecasts']:
            forecast_date = datetime.strptime(daily['date'].split('T')[0], '%Y-%m-%d').date()

            if forecast_date == target_date:
                # Calculate average temperature
                avg_temp = (daily['min_temp'] + daily['max_temp']) / 2

                # Determine if it's suitable for lawn care
                is_suitable = True
                precipitation_warning = None

                # Check precipitation probability
                if daily['day_precipitation_probability'] > 50:
                    is_suitable = False
                    precipitation_warning = f"High chance of {daily['day_precipitation_type']} ({daily['day_precipitation_probability']}%)"

                # Format the weather data
                weather_data = {
                    'date': date_str,
                    'min_temp': daily['min_temp'],
                    'max_temp': daily['max_temp'],
                    'avg_temp': avg_temp,
                    'condition': daily['day_phrase'],
                    'icon': daily['day_icon'],
                    'precipitation_probability': daily['day_precipitation_probability'],
                    'precipitation_type': daily['day_precipitation_type'],
                    'is_suitable_for_lawn_care': is_suitable,
                    'warning': precipitation_warning,
                    'wind_speed': 10  # Default value as AccuWeather daily forecast doesn't include wind speed
                }

                logger.info(f"Successfully retrieved weather for {city} on {date_str}")
                return weather_data

        # If we get here, the date wasn't found in the forecast
        logger.warning(f"No forecast available for {date_str} in {city}")
        return None

    except Exception as e:
        logger.error(f"Error getting weather for date: {e}")
        return None

def get_weather_icon_class(icon_code):
    """
    Convert AccuWeather icon code to Bootstrap icon class.

    Args:
        icon_code (int): AccuWeather icon code

    Returns:
        str: Bootstrap icon class
    """
    # Map AccuWeather icon codes to Bootstrap icons
    # Reference: https://developer.accuweather.com/weather-icons
    icon_map = {
        # Sunny
        1: "bi-sun",
        2: "bi-sun",
        3: "bi-sun",
        4: "bi-sun",
        5: "bi-cloud-sun",
        # Partly cloudy
        6: "bi-cloud-sun",
        7: "bi-cloud-sun",
        8: "bi-cloud",
        # Cloudy
        11: "bi-cloud",
        # Showers
        12: "bi-cloud-drizzle",
        13: "bi-cloud-drizzle",
        14: "bi-cloud-rain",
        # Thunderstorms
        15: "bi-cloud-lightning",
        16: "bi-cloud-lightning",
        17: "bi-cloud-lightning-rain",
        # Rain
        18: "bi-cloud-rain",
        # Flurries
        19: "bi-cloud-snow",
        20: "bi-cloud-snow",
        21: "bi-cloud-snow",
        22: "bi-cloud-snow",
        # Snow
        23: "bi-snow",
        24: "bi-snow",
        25: "bi-snow",
        26: "bi-snow",
        # Ice
        29: "bi-snow",
        # Rain and snow
        30: "bi-cloud-sleet",
        # Hot
        31: "bi-thermometer-high",
        # Cold
        32: "bi-thermometer-low",
        # Windy
        33: "bi-wind",
        34: "bi-wind",
        # Clear night
        35: "bi-moon",
        36: "bi-moon",
        37: "bi-moon",
        38: "bi-cloud-moon",
        # Partly cloudy night
        39: "bi-cloud-moon",
        40: "bi-cloud-moon",
        41: "bi-cloud-moon",
        42: "bi-cloud",
        # Night showers
        43: "bi-cloud-drizzle",
        44: "bi-cloud-rain",
    }

    return icon_map.get(icon_code, "bi-cloud-question")

def get_lawn_care_recommendation(weather_data):
    """
    Get lawn care recommendations based on weather data.

    Args:
        weather_data (dict): Weather data

    Returns:
        dict: Recommendations
    """
    if not weather_data:
        return {
            'can_mow': False,
            'message': "Weather data not available",
            'details': []
        }

    can_mow = True
    messages = []
    details = []

    # Check precipitation
    if weather_data['precipitation_probability'] > 60:
        can_mow = False
        messages.append("High chance of precipitation")
        details.append(f"{weather_data['precipitation_probability']}% chance of {weather_data['precipitation_type'] or 'precipitation'}")

    # Check temperature
    if weather_data['max_temp'] > 35:
        can_mow = False
        messages.append("Temperature too high")
        details.append(f"Maximum temperature of {weather_data['max_temp']}°C may cause heat stress to grass")
    elif weather_data['max_temp'] < 5:
        can_mow = False
        messages.append("Temperature too low")
        details.append(f"Maximum temperature of {weather_data['max_temp']}°C is too cold for optimal lawn care")

    # If can mow, add positive message
    if can_mow:
        messages.append("Weather conditions suitable for lawn care")

        # Add specific recommendations based on conditions
        if weather_data['max_temp'] > 28:
            details.append("Consider mowing in the morning or evening to avoid heat")

        if weather_data['precipitation_probability'] > 20:
            details.append("There's a slight chance of precipitation, monitor weather before service")

    return {
        'can_mow': can_mow,
        'message': "; ".join(messages),
        'details': details
    }

# Example usage
if __name__ == "__main__":
    # Set your API key here for testing
    # os.environ['ACCUWEATHER_API_KEY'] = 'your-api-key'

    city = "Johannesburg"
    location_key = get_location_key(city)

    if location_key:
        print(f"Location key for {city}: {location_key}")

        # Get current weather
        current = get_current_weather(location_key)
        if current:
            print("\nCurrent Weather:")
            print(f"Temperature: {current['temperature']}°{current['temperature_unit']}")
            print(f"Condition: {current['weather_text']}")
            print(f"Humidity: {current['relative_humidity']}%")
            print(f"Wind: {current['wind_speed']} {current['wind_unit']}")

        # Get forecast
        forecast = get_forecast(location_key)
        if forecast:
            print("\nForecast Headline:")
            print(forecast['headline'])

            print("\n5-Day Forecast:")
            for day in forecast['daily_forecasts']:
                date = day['date'].split('T')[0]
                print(f"\n{date}:")
                print(f"Temperature: {day['min_temp']}°C - {day['max_temp']}°C")
                print(f"Day: {day['day_phrase']}")
                print(f"Night: {day['night_phrase']}")
                print(f"Precipitation Probability: {day['day_precipitation_probability']}%")

