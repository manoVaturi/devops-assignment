from app.helpers import (
    extract_location,
    filter_city_data,
    get_city_data,
    search_cities,
)


def test_search_cities_prefix_first():
    results = search_cities("tel aviv")
    assert results
    assert results[0].lower().startswith("tel aviv")


def test_search_cities_empty_query():
    assert search_cities("") == []
    assert search_cities("   ") == []


def test_search_cities_limit():
    assert len(search_cities("a", limit=3)) == 3


def test_get_city_data_valid():
    label = search_cities("london")[0]
    city = get_city_data(label)
    assert city is not None
    assert city.name.lower().startswith("london")
    assert -90 <= city.latitude <= 90


def test_get_city_data_invalid():
    assert get_city_data(None) is None
    assert get_city_data("no comma") is None
    assert get_city_data("Atlantis, XX") is None


def test_filter_city_data():
    raw = {
        "forecast": {
            "forecastday": [
                {
                    "date": "2026-10-12",
                    "day": {
                        "mintemp_c": 18.0,
                        "maxtemp_c": 27.5,
                        "avghumidity": 60,
                        "condition": {"icon": "//cdn/sun.png"},
                    },
                }
            ]
        }
    }
    assert filter_city_data(raw) == [
        {
            "day": "Monday",
            "date": "2026-10-12",
            "min_c": 18.0,
            "max_c": 27.5,
            "humidity": 60,
            "icon": "//cdn/sun.png",
        }
    ]


def test_filter_city_data_bad_date():
    raw = {"forecast": {"forecastday": [{"date": "not-a-date", "day": {}}]}}
    assert filter_city_data(raw)[0]["day"] == ""


def test_extract_location_defaults():
    assert extract_location({}) == {"name": "Unknown", "country": ""}
