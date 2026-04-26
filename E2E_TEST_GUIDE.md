# End-to-End Test Guide

This guide verifies the completed workflow:

`User Login -> Job Creation -> CV Upload -> RabbitMQ -> AI Scoring -> RabbitMQ -> Notification -> Frontend Display`

## 1. Start the microservices

From `cv_service/docker-compose.yml` run:

If you want real verification emails instead of console-only codes, create `cv_service/.env` from `cv_service/.env.example` first and fill in your SMTP credentials. If `cv_service/.env` is missing, the auth service falls back to the console email backend and no real email will be delivered.

```powershell
cd C:\Users\safsa\Desktop\New folder\cvservice\cv_service
copy .env.example .env
# edit .env with your SMTP values
docker compose up --build
```

Important:

- After creating or editing `cv_service/.env`, restart the stack from the `cv_service` folder so Docker picks up the new environment values.
- For Gmail, `AUTH_EMAIL_HOST_USER` must be your exact Gmail address and `AUTH_EMAIL_HOST_PASSWORD` must be a 16-character Google App Password, not your normal Gmail password.

Expected public endpoints:

- Auth service: `http://127.0.0.1:8001`
- Job service: `http://127.0.0.1:8002`
- CV service: `http://127.0.0.1:8000`
- RabbitMQ dashboard: `http://127.0.0.1:15672`

## 2. Serve the frontend on port 5173

In a second terminal:

```powershell
cd C:\Users\safsa\Desktop\New folder\cvservice\auth-service-django-main\frontend
python -m http.server 5173 --bind 127.0.0.1
```

Open:

```text
http://127.0.0.1:5173
```

## 3. Browser workflow

1. Register a recruiter account from `register.html`.
2. If SMTP is configured, check your inbox for the 6-digit verification code. If SMTP is not configured, the UI will show the dev code directly.
3. Verify the email from `verify-email.html`.
4. Log in from `login.html` if you did not auto-redirect.
5. Create a job from the recruiter dashboard.
6. Upload `cv_service/sample_cv.pdf` against the created job id.
7. Watch the Rankings panel poll `GET http://127.0.0.1:8000/api/job/<job_id>/`.
8. Confirm that the uploaded CV changes from `Processing` to `Scored`.

## 4. Automated API smoke test

Run the PowerShell script from the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\e2e_workflow_test.ps1
```

What the script does:

1. Registers a unique user through the auth service.
2. Logs in and captures a JWT access token.
3. Creates a job through the job service using `Authorization: Bearer <token>`.
4. Uploads a PDF CV through the CV service with the same JWT.
5. Polls the CV ranking endpoint until a score is present.
6. Checks notification-service logs for a `cv_scored_notification` event when Docker is available.

## 5. Success checks

The system is healthy when all of these are true:

- `POST /api/auth/login/` returns an access token.
- `POST /api/jobs/` returns a real numeric job id.
- `POST /api/upload/` returns `status: processing`.
- The AI worker logs `cv_scored`.
- The notification service logs `cv_scored_notification`.
- `GET /api/job/<job_id>/` returns the uploaded CV with a non-null `score`.
- The dashboard ranking table refreshes automatically in the browser.

## 6. Useful log commands

```powershell
cd C:\Users\safsa\Desktop\New folder\cvservice\cv_service
docker compose logs -f ai_worker
docker compose logs -f notification_service
docker compose logs -f cv_service
```

## 7. Expected notification evidence

The notification log now emits structured JSON. A successful message looks like:

```json
{"event":"cv_scored_notification","cv_id":1,"job_id":"1","score":0.73}
```
