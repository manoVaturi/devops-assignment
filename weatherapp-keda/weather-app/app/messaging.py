import json
import os
import threading
import uuid

import pika
from pika.exceptions import AMQPError

QUEUE_NAME = "weather_requests_queue"
RPC_TIMEOUT_SECONDS = 45

# one connection per gunicorn thread, reused between requests
_local = threading.local()


class RpcError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def queue_enabled() -> bool:
    return bool(os.environ.get("RABBITMQ_URL"))


def connect() -> pika.BlockingConnection:
    return pika.BlockingConnection(
        pika.URLParameters(os.environ["RABBITMQ_URL"])
    )


def _channel():
    connection = getattr(_local, "connection", None)
    if connection is None or connection.is_closed:
        connection = connect()
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        _local.reply_queue = channel.queue_declare(
            queue="", exclusive=True
        ).method.queue
        _local.connection, _local.channel = connection, channel
    return _local.channel, _local.reply_queue


def _reset():
    connection = getattr(_local, "connection", None)
    _local.connection = None
    if connection is not None and connection.is_open:
        try:
            connection.close()
        except AMQPError:
            pass


def _call(query: str) -> dict:
    channel, reply_queue = _channel()
    correlation_id = str(uuid.uuid4())
    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=json.dumps({"query": query}),
        properties=pika.BasicProperties(
            reply_to=reply_queue,
            correlation_id=correlation_id,
            expiration=str(RPC_TIMEOUT_SECONDS * 1000),
        ),
    )
    try:
        for _, properties, body in channel.consume(
            reply_queue, auto_ack=True, inactivity_timeout=RPC_TIMEOUT_SECONDS
        ):
            if body is None or properties is None:
                break
            # replies to older, timed out requests are skipped
            if properties.correlation_id == correlation_id:
                reply = json.loads(body)
                if "error" in reply:
                    raise RpcError(reply["error"], reply["status_code"])
                return reply
    finally:
        if channel.is_open:
            channel.cancel()
    raise RpcError("Timed out waiting for a worker. Please try again.", 504)


def request_forecast(query: str) -> dict:
    # publish the request and wait for the worker reply.
    # an idle connection can be closed by the broker, so retry once
    for attempt in (1, 2):
        try:
            return _call(query)
        except AMQPError as exc:
            _reset()
            if attempt == 2:
                raise RpcError("Message queue is unavailable.", 503) from exc
