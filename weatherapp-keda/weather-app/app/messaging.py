import json
import os
import uuid

import pika
from pika.exceptions import AMQPError

QUEUE_NAME = "weather_requests_queue"
RPC_TIMEOUT_SECONDS = 45


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


def request_forecast(query: str) -> dict:
    # publish the request and wait for the worker reply
    try:
        connection = connect()
    except AMQPError as exc:
        raise RpcError("Message queue is unavailable.", 503) from exc

    with connection:
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        reply_queue = channel.queue_declare(
            queue="", exclusive=True
        ).method.queue

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

        for _, properties, body in channel.consume(
            reply_queue, auto_ack=True, inactivity_timeout=RPC_TIMEOUT_SECONDS
        ):
            if body is None or properties is None:
                break
            if properties.correlation_id == correlation_id:
                reply = json.loads(body)
                if "error" in reply:
                    raise RpcError(reply["error"], reply["status_code"])
                return reply

    raise RpcError("Timed out waiting for a worker. Please try again.", 504)
