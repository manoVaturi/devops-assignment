import json
from types import SimpleNamespace

import pytest
from app import messaging
from pika.exceptions import AMQPConnectionError, StreamLostError


@pytest.fixture(autouse=True)
def fresh_thread_state():
    messaging._local.__dict__.clear()
    yield
    messaging._local.__dict__.clear()


def fake_connection(mocker, replies):
    """A connection whose channel answers the next publish with `replies`."""
    connection = mocker.MagicMock(is_closed=False, is_open=True)
    channel = connection.channel.return_value
    channel.is_open = True
    channel.queue_declare.return_value.method.queue = "amq.gen-reply"

    def consume(*args, **kwargs):
        sent = channel.basic_publish.call_args.kwargs["properties"]
        for reply in replies:
            if reply is None:
                yield None, None, None
                continue
            correlation_id = reply.pop("_cid", sent.correlation_id)
            yield None, SimpleNamespace(correlation_id=correlation_id), (
                json.dumps(reply)
            )

    channel.consume.side_effect = consume
    return connection


def test_reply_is_returned(mocker):
    reply = {"forecast": [], "location": {}}
    connection = fake_connection(mocker, [dict(reply)])
    mocker.patch.object(messaging, "connect", return_value=connection)

    assert messaging.request_forecast("1,2") == reply

    channel = connection.channel.return_value
    publish = channel.basic_publish.call_args.kwargs
    assert publish["routing_key"] == messaging.QUEUE_NAME
    assert publish["properties"].reply_to == "amq.gen-reply"
    assert json.loads(publish["body"]) == {"query": "1,2"}
    channel.cancel.assert_called_once_with()


def test_connection_is_reused(mocker):
    connection = fake_connection(mocker, [{"forecast": []}])
    connect = mocker.patch.object(
        messaging, "connect", return_value=connection
    )

    messaging.request_forecast("1,2")
    messaging.request_forecast("3,4")

    connect.assert_called_once_with()


def test_old_replies_are_skipped(mocker):
    connection = fake_connection(
        mocker,
        [{"_cid": "old", "forecast": "stale"}, {"forecast": []}],
    )
    mocker.patch.object(messaging, "connect", return_value=connection)

    assert messaging.request_forecast("1,2")["forecast"] == []


def test_worker_error_is_raised(mocker):
    connection = fake_connection(
        mocker,
        [{"error": "Failed to fetch weather data.", "status_code": 502}],
    )
    mocker.patch.object(messaging, "connect", return_value=connection)

    with pytest.raises(messaging.RpcError) as exc:
        messaging.request_forecast("1,2")
    assert exc.value.status_code == 502


def test_timeout(mocker):
    connection = fake_connection(mocker, [None])
    mocker.patch.object(messaging, "connect", return_value=connection)

    with pytest.raises(messaging.RpcError) as exc:
        messaging.request_forecast("1,2")
    assert exc.value.status_code == 504


def test_dropped_connection_is_replaced(mocker):
    stale = fake_connection(mocker, [])
    stale.channel.return_value.basic_publish.side_effect = StreamLostError()
    fresh = fake_connection(mocker, [{"forecast": []}])
    connect = mocker.patch.object(
        messaging, "connect", side_effect=[stale, fresh]
    )

    assert messaging.request_forecast("1,2") == {"forecast": []}
    assert connect.call_count == 2


def test_broker_down(mocker):
    mocker.patch.object(
        messaging, "connect", side_effect=AMQPConnectionError()
    )

    with pytest.raises(messaging.RpcError) as exc:
        messaging.request_forecast("1,2")
    assert exc.value.status_code == 503
