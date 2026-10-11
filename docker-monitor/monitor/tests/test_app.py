from types import SimpleNamespace

import pytest
from app.app import app
from docker.errors import DockerException


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Live Docker Monitor" in response.data


def test_containers_lists_running_containers(client, mocker):
    docker_client = mocker.patch("app.app.docker.from_env").return_value
    docker_client.containers.list.return_value = [
        SimpleNamespace(
            short_id="abc1234",
            name="fake-nginx",
            status="running",
        )
    ]

    response = client.get("/containers")

    assert response.status_code == 200
    assert response.get_json() == {
        "containers": [
            {
                "id": "abc1234",
                "name": "fake-nginx",
                "status": "running",
            }
        ]
    }
    # running containers only
    docker_client.containers.list.assert_called_once_with()
    # client is closed after each request
    docker_client.close.assert_called_once_with()


def test_containers_reports_docker_errors(client, mocker):
    mocker.patch(
        "app.app.docker.from_env",
        side_effect=DockerException("no socket"),
    )

    response = client.get("/containers")

    assert response.status_code == 503
    assert "no socket" in response.get_json()["error"]
