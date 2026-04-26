# CV Service Testing Guide

This service is now part of the full secured workflow documented in `..\E2E_TEST_GUIDE.md`.

## Public endpoints

- `POST /api/upload/`
- `GET /api/job/<job_id>/`
- `GET /api/cv/job/<job_id>/`

All public endpoints require:

```text
Authorization: Bearer <jwt>
```

## Internal endpoint

- `PATCH /api/internal/cv/<cv_id>/score/`

Internal calls must send:

```text
X-Internal-Token: <shared token>
```

## Local verification

1. Start the full stack with `docker compose up --build` from `cv_service`.
2. Use the frontend on `http://127.0.0.1:5173` or run `..\e2e_workflow_test.ps1`.
3. Confirm that `GET /api/job/<job_id>/` returns scored CVs once the AI worker finishes.
