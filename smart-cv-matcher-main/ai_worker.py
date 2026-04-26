import json
import logging
import os
import time

import pika
import requests

from app import calculate_score


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(message)s")
logger = logging.getLogger("ai_worker")

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
CV_SCORING_QUEUE = os.getenv(
    "RABBITMQ_CV_SCORING_QUEUE",
    os.getenv("CV_SCORING_QUEUE", "cv_scoring_queue"),
)
CV_RESULTS_QUEUE = os.getenv(
    "RABBITMQ_CV_RESULTS_QUEUE",
    os.getenv("CV_RESULTS_QUEUE", "cv_results_queue"),
)
CV_SERVICE_URL = os.getenv("CV_SERVICE_URL", "http://cv_service:8000")
JOB_SERVICE_URL = os.getenv("JOB_SERVICE_URL", "http://job_service:8000")
CV_SERVICE_HOST_HEADER = os.getenv("CV_SERVICE_HOST_HEADER", "localhost")
JOB_SERVICE_HOST_HEADER = os.getenv("JOB_SERVICE_HOST_HEADER", "localhost")
INTERNAL_API_TOKEN = os.getenv("INTERNAL_API_TOKEN", "change-me-in-production")
INTERNAL_API_TIMEOUT = float(os.getenv("INTERNAL_API_TIMEOUT", "5"))


class RetryableProcessingError(Exception):
    pass


class NonRetryableProcessingError(Exception):
    pass


def log_event(event, **payload):
    logger.info(json.dumps({"event": event, **payload}))


def connection_parameters():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    return pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
        client_properties={"connection_name": "ai-worker-cv-scoring"},
        heartbeat=600,
        blocked_connection_timeout=300,
        connection_attempts=3,
        retry_delay=2,
    )


def internal_headers(host_header):
    return {
        "X-Internal-Token": INTERNAL_API_TOKEN,
        "Host": host_header,
    }


def publish_result(channel, payload):
    channel.queue_declare(queue=CV_RESULTS_QUEUE, durable=True)
    channel.basic_publish(
        exchange="",
        routing_key=CV_RESULTS_QUEUE,
        body=json.dumps(payload).encode("utf-8"),
        properties=pika.BasicProperties(
            content_type="application/json",
            delivery_mode=2,
        ),
    )
    log_event(
        "cv_scoring_result_published",
        cv_id=payload["cv_id"],
        job_id=payload["job_id"],
        score=payload["score"],
        queue=CV_RESULTS_QUEUE,
    )


def fetch_job_payload(job_id):
    try:
        response = requests.get(
            f"{JOB_SERVICE_URL}/api/internal/jobs/{job_id}/",
            headers=internal_headers(JOB_SERVICE_HOST_HEADER),
            timeout=INTERNAL_API_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise RetryableProcessingError("Job service request failed.") from exc

    if response.status_code == 404:
        raise NonRetryableProcessingError(f"Job {job_id} was not found.")
    if response.status_code >= 500:
        raise RetryableProcessingError("Job service returned a server error.")
    if response.status_code != 200:
        raise NonRetryableProcessingError(
            f"Unexpected job service status code {response.status_code}."
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise RetryableProcessingError("Job service returned invalid JSON.") from exc

    description = (payload.get("description") or "").strip()
    title = (payload.get("title") or "").strip()
    job_text = "\n".join(part for part in [title, description] if part)
    if not job_text:
        raise NonRetryableProcessingError(
            f"Job {job_id} does not contain a description for scoring."
        )

    return payload, job_text


def update_cv_score(cv_id, score):
    try:
        response = requests.patch(
            f"{CV_SERVICE_URL}/api/internal/cv/{cv_id}/score/",
            json={"score": score},
            headers=internal_headers(CV_SERVICE_HOST_HEADER),
            timeout=INTERNAL_API_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise RetryableProcessingError("CV service update request failed.") from exc

    if response.status_code == 404:
        raise NonRetryableProcessingError(f"CV {cv_id} was not found.")
    if response.status_code >= 500:
        raise RetryableProcessingError("CV service returned a server error.")
    if response.status_code != 200:
        raise NonRetryableProcessingError(
            f"Unexpected CV service status code {response.status_code}."
        )


def handle_cv_message(channel, method, properties, body):
    try:
        message = json.loads(body.decode("utf-8"))
        cv_id = message["cv_id"]
        job_id = message["job_id"]
        cv_text = message["cv_text"]

        log_event("cv_scoring_message_received", cv_id=cv_id, job_id=job_id)

        job_payload, job_text = fetch_job_payload(job_id)
        score = calculate_score(job_text, cv_text)
        update_cv_score(cv_id, score)

        result = {
            "cv_id": cv_id,
            "job_id": job_id,
            "score": score,
        }
        publish_result(channel, result)
        channel.basic_ack(delivery_tag=method.delivery_tag)

        log_event(
            "cv_scored",
            cv_id=cv_id,
            job_id=job_id,
            score=score,
            job_title=job_payload.get("title", ""),
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        log_event("cv_scoring_invalid_message", error=str(exc), body=body.decode("utf-8", errors="replace"))
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except NonRetryableProcessingError as exc:
        log_event("cv_scoring_non_retryable_error", error=str(exc))
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except RetryableProcessingError as exc:
        log_event("cv_scoring_retryable_error", error=str(exc))
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    except Exception as exc:
        log_event("cv_scoring_unexpected_error", error=str(exc))
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def start_worker():
    while True:
        connection = None
        try:
            log_event("rabbitmq_connecting", host=RABBITMQ_HOST, port=RABBITMQ_PORT)
            connection = pika.BlockingConnection(connection_parameters())
            channel = connection.channel()
            channel.queue_declare(queue=CV_SCORING_QUEUE, durable=True)
            channel.queue_declare(queue=CV_RESULTS_QUEUE, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue=CV_SCORING_QUEUE,
                on_message_callback=handle_cv_message,
                auto_ack=False,
                consumer_tag="ai-worker-cv-scoring",
            )

            log_event("ai_worker_listening", queue=CV_SCORING_QUEUE)
            channel.start_consuming()
        except KeyboardInterrupt:
            log_event("ai_worker_stopping")
            if connection and connection.is_open:
                connection.close()
            break
        except (pika.exceptions.AMQPError, OSError) as exc:
            log_event("rabbitmq_connection_failed", error=str(exc), retry_in_seconds=5)
            time.sleep(5)
        finally:
            if connection and connection.is_open:
                connection.close()


if __name__ == "__main__":
    start_worker()
