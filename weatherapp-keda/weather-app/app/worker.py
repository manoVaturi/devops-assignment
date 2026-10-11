import json
import logging

import pika

from .app import WeatherServiceError, _fetch_forecast
from .messaging import QUEUE_NAME, connect

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("worker")


def handle_request(channel, method, properties, body):
    query = json.loads(body)["query"]
    try:
        forecast, location = _fetch_forecast(query)
        reply = {"forecast": forecast, "location": location}
    except WeatherServiceError as exc:
        reply = {"error": exc.message, "status_code": exc.status_code}

    channel.basic_publish(
        exchange="",
        routing_key=properties.reply_to,
        body=json.dumps(reply),
        properties=pika.BasicProperties(
            correlation_id=properties.correlation_id
        ),
    )
    channel.basic_ack(delivery_tag=method.delivery_tag)


def main():
    connection = connect()
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    # one message at a time so the rest stays in the queue (KEDA counts it)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=handle_request)
    log.info("Waiting for messages on %s", QUEUE_NAME)
    channel.start_consuming()


if __name__ == "__main__":
    main()
