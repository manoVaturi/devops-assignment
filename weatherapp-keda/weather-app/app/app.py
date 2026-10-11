import os
import time
from collections import OrderedDict

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from . import messaging
from .helpers import (
    City,
    extract_location,
    filter_city_data,
    get_city_data,
    search_cities,
)

# WEATHER_API_KEY=your_weatherapi_key_here
load_dotenv()

app = Flask(__name__)


WEATHER_API_URL = "https://api.weatherapi.com/v1/forecast.json"
REQUEST_TIMEOUT_SECONDS = 10
FORECAST_CACHE_TTL_SECONDS = 600
FORECAST_CACHE_MAX_ENTRIES = 256


http = requests.Session()

_forecast_cache: "OrderedDict[str, tuple[float, tuple[list[dict], dict]]]" = (
    OrderedDict()
)


class WeatherServiceError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _fetch_forecast(query: str) -> tuple[list[dict], dict]:

    cached = _forecast_cache.get(query)
    if cached and time.monotonic() - cached[0] < FORECAST_CACHE_TTL_SECONDS:
        _forecast_cache.move_to_end(query)
        return cached[1]

    api_key = os.environ.get("WEATHER_API_KEY")
    if not api_key:
        raise WeatherServiceError("Weather API key not configured.", 500)

    params = {
        "key": api_key,
        "q": query,
        "days": 7,
        "aqi": "no",
        "alerts": "no",
    }
    try:
        response = http.get(
            WEATHER_API_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS
        )
    except requests.exceptions.RequestException as exc:
        app.logger.error("Weather API request failed: %s", exc)
        raise WeatherServiceError(
            "Could not reach the weather service. Please try again shortly.",
            503,
        ) from exc

    if response.status_code != 200:
        app.logger.warning(
            "Weather API returned %s: %s", response.status_code, response.text
        )
        raise WeatherServiceError(
            "Failed to fetch weather data.", response.status_code
        )

    payload = response.json()
    result = (filter_city_data(payload), payload.get("location", {}))
    _forecast_cache[query] = (time.monotonic(), result)
    _forecast_cache.move_to_end(query)
    if len(_forecast_cache) > FORECAST_CACHE_MAX_ENTRIES:
        _forecast_cache.popitem(last=False)
    return result


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _valid_coordinates(latitude, longitude) -> bool:
    return (
        _is_number(latitude)
        and _is_number(longitude)
        and -90 <= latitude <= 90
        and -180 <= longitude <= 180
    )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/cities")
def get_cities():
    query = request.args.get("q", "")
    return jsonify(search_cities(query))


@app.route("/api/weather", methods=["POST"])
def api_weather():
    payload = request.get_json(silent=True) or {}
    city_input = payload.get("city")
    latitude, longitude = payload.get("latitude"), payload.get("longitude")

    location: dict | None = None
    if city_input:
        city: City | None = get_city_data(city_input)
        if not city:
            return jsonify({"error": "Invalid city selected."}), 400
        query = f"{city.latitude},{city.longitude}"
        location = {"name": city.name, "country": city.country_code}
    elif _valid_coordinates(latitude, longitude):
        query = f"{latitude},{longitude}"
    else:
        return jsonify({"error": "Provide a valid city or coordinates."}), 400

    try:
        if messaging.queue_enabled():
            reply = messaging.request_forecast(query)
            forecast, raw_location = reply["forecast"], reply["location"]
        else:
            forecast, raw_location = _fetch_forecast(query)
    except (WeatherServiceError, messaging.RpcError) as exc:
        return jsonify({"error": exc.message}), exc.status_code

    if location is None:
        location = extract_location(raw_location)

    return jsonify({"city": location, "forecast": forecast})


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode)
