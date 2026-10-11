import bisect
from dataclasses import dataclass
from datetime import date

import geonamescache

gc = geonamescache.GeonamesCache()


@dataclass(frozen=True)
class City:
    name: str
    latitude: float
    longitude: float
    country_code: str


def _build_city_index() -> tuple[dict, list[str], list[str]]:

    by_label = {
        f"{details['name']}, {details['countrycode']}": details
        for details in gc.get_cities().values()
    }
    pairs = sorted((label.lower(), label) for label in by_label)
    return by_label, [p[0] for p in pairs], [p[1] for p in pairs]


_CITY_BY_LABEL, _SORTED_LOWER, _SORTED_LABELS = _build_city_index()


def search_cities(query: str, limit: int = 5) -> list[str]:
    query = (query or "").lower().strip()
    if not query:
        return []

    start = bisect.bisect_left(_SORTED_LOWER, query)
    end = bisect.bisect_left(_SORTED_LOWER, query + "￿")
    prefix_matches = _SORTED_LABELS[start:end]

    if len(prefix_matches) >= limit:
        return prefix_matches[:limit]

    contains_matches = [
        label
        for lower, label in zip(_SORTED_LOWER, _SORTED_LABELS)
        if query in lower and not lower.startswith(query)
    ]
    return (prefix_matches + contains_matches)[:limit]


def get_city_data(user_input: str | None) -> City | None:
    if not user_input or "," not in user_input:
        return None

    city_details = _CITY_BY_LABEL.get(user_input.strip())
    if not city_details:
        return None

    return City(
        name=city_details.get("name", ""),
        latitude=city_details.get("latitude", 0.0),
        longitude=city_details.get("longitude", 0.0),
        country_code=city_details.get("countrycode", ""),
    )


def filter_city_data(raw_data: dict) -> list[dict]:
    forecast_days = raw_data.get("forecast", {}).get("forecastday", [])
    filtered_data = []

    for item in forecast_days:
        date_str = item.get("date")
        try:
            day_name = date.fromisoformat(date_str).strftime("%A")
        except (TypeError, ValueError):
            day_name = ""

        daily_temps = item.get("day", {})
        filtered_data.append(
            {
                "day": day_name,
                "date": date_str,
                "min_c": daily_temps.get("mintemp_c"),
                "max_c": daily_temps.get("maxtemp_c"),
                "humidity": daily_temps.get("avghumidity"),
                "icon": daily_temps.get("condition", {}).get("icon"),
            }
        )
    return filtered_data


def extract_location(location: dict) -> dict:

    return {
        "name": location.get("name") or "Unknown",
        "country": location.get("country") or "",
    }
