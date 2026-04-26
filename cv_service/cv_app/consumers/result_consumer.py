import json
import logging
import time

import pika
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import close_old_connections

from cv_app.models import CV
from cv_app.producers.cv_producer import _connection_parameters


logger = logging.getLogger(__name__)


def _handle_result_message(channel, method, properties, body):
    close_old_connections()

    try:
        payload = json.loads(body.decode("utf-8"))
        cv_id = payload["cv_id"]
        score = float(payload["score"])

        updated = CV.objects.filter(cv_id=cv_id).update(score=score)
        if updated:
            logger.info("Updated CV %s with score %s", cv_id, score)
        else:
            logger.warning("Received result for unknown CV id %s", cv_id)

        channel.basic_ack(delivery_tag=method.delivery_tag)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError, ValidationError):
        logger.exception("Invalid result message: %s", body)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception:
        logger.exception("Failed to process result message")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    finally:
        close_old_connections()


def start_result_consumer():
    queue_name = settings.RABBITMQ_CV_RESULTS_QUEUE

    while True:
        connection = None
        try:
            connection = pika.BlockingConnection(_connection_parameters())
            channel = connection.channel()
            channel.queue_declare(queue=queue_name, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue=queue_name,
                on_message_callback=_handle_result_message,
            )

            logger.info("Listening for CV results on queue %s", queue_name)
            channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Stopping CV result consumer")
            if connection and connection.is_open:
                connection.close()
            break
        except (pika.exceptions.AMQPError, OSError):
            logger.exception("RabbitMQ connection failed. Retrying in 5 seconds.")
            time.sleep(5)
        finally:
            if connection and connection.is_open:
                connection.close()
