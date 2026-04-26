import requests
from django.conf import settings


class JobServiceError(Exception):
    pass


class JobNotFoundError(JobServiceError):
    pass


def fetch_job(job_id):
    response = None
    try:
        response = requests.get(
            f"{settings.JOB_SERVICE_URL}/api/internal/jobs/{job_id}/",
            headers={
                "X-Internal-Token": settings.INTERNAL_API_TOKEN,
                "Host": settings.JOB_SERVICE_HOST_HEADER,
            },
            timeout=settings.INTERNAL_API_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise JobServiceError("Job service request failed.") from exc

    if response.status_code == 404:
        raise JobNotFoundError(f"Job {job_id} was not found.")

    try:
        response.raise_for_status()
        return response.json()
    except ValueError as exc:
        raise JobServiceError("Job service returned invalid JSON.") from exc
    except requests.RequestException as exc:
        raise JobServiceError("Job service returned an error.") from exc
