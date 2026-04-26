import json
import logging

import pika
from django.conf import settings


logger = logging.getLogger(__name__)


class RabbitMQPublishError(Exception):
    pass


def _connection_parameters():
    credentials = pika.PlainCredentials(
        settings.RABBITMQ_USER,
        settings.RABBITMQ_PASSWORD,
    )
    return pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        virtual_host=settings.RABBITMQ_VHOST,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
        connection_attempts=3,
        retry_delay=2,
    )


def _numeric_id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def publish_cv_for_scoring(cv_id, cv_text, job_id):
    queue_name = settings.RABBITMQ_CV_SCORING_QUEUE
    message = {
        "cv_id": cv_id,
        "cv_text": cv_text,
        "job_id": _numeric_id(job_id),
    }

    connection = None
    try:
        connection = pika.BlockingConnection(_connection_parameters())
        channel = connection.channel()
        channel.queue_declare(queue=queue_name, durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=json.dumps(message).encode("utf-8"),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
            ),
        )
        logger.info(
            json.dumps(
                {
                    "event": "cv_scoring_event_published",
                    "cv_id": cv_id,
                    "job_id": message["job_id"],
                    "queue": queue_name,
                }
            )
        )
    except (pika.exceptions.AMQPError, OSError) as exc:
        logger.exception("Failed to publish CV %s to RabbitMQ", cv_id)
        raise RabbitMQPublishError("RabbitMQ publish failed.") from exc
    finally:
        if connection and connection.is_open:
            connection.close()
