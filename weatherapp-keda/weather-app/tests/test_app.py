import pytest
from app import messaging
from app.app import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_cities(client):
    response = client.get("/api/cities?q=paris")
    assert response.status_code == 200
    assert any(c.startswith("Paris") for c in response.get_json())


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"city": "Atlantis, XX"},
        {"latitude": 91, "longitude": 0},
        {"latitude": "32", "longitude": "34"},
        {"latitude": True, "longitude": 0},
    ],
)
def test_weather_rejects_bad_input(client, payload):
    response = client.post("/api/weather", json=payload)
    assert response.status_code == 400


def test_weather_goes_through_the_queue(client, mocker):
    rpc = mocker.patch(
        "app.app.messaging.request_forecast",
        return_value={
            "forecast": [{"day": "Monday"}],
            "location": {"name": "Haifa", "country": "Israel"},
        },
    )

    response = client.post(
        "/api/weather", json={"latitude": 32.8, "longitude": 35.0}
    )

    assert response.status_code == 200
    rpc.assert_called_once_with("32.8,35.0")
    assert response.get_json() == {
        "city": {"name": "Haifa", "country": "Israel"},
        "forecast": [{"day": "Monday"}],
    }


def test_weather_queue_error(client, mocker):
    mocker.patch(
        "app.app.messaging.request_forecast",
        side_effect=messaging.RpcError("Timed out waiting for a worker.", 504),
    )

    response = client.post(
        "/api/weather", json={"latitude": 32.8, "longitude": 35.0}
    )

    assert response.status_code == 504
    assert "Timed out" in response.get_json()["error"]
