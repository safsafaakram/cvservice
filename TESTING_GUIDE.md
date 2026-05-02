# Testing Guide

This guide matches the current project structure:

- frontend files in `frontend/`
- local Docker Compose in `deploy/`
- current mixed setup:
  - local `auth_service`
  - Railway `job_service`
  - local `cv_service`
  - local `rabbitmq`
  - local `ai_worker`
  - local `notification_service`

## 1. Current API Setup

The frontend is currently configured to use:

- Auth API: `http://127.0.0.1:8001/api/auth`
- Job API: `https://romantic-commitment-production.up.railway.app/api`
- CV API: `http://127.0.0.1:8000/api`

The local CV service and AI worker are also configured to call the Railway job service.

## 2. Before You Start

Make sure Docker Desktop is running.

If you changed browser users or tokens before, clear saved browser storage:

```js
localStorage.clear()
```

You can run that in the browser DevTools Console after opening the frontend.

## 3. Start The Local Backend Services

Open PowerShell and run:

```powershell
cd "C:\Users\safsa\Desktop\New folder\cvservice\deploy"
docker compose up --build
```

This starts:

- `auth_service` on `http://127.0.0.1:8001`
- `cv_service` on `http://127.0.0.1:8000`
- `rabbitmq` on `http://127.0.0.1:15672`
- local `ai_worker`
- local `notification_service`

`job_service` is not expected locally in the current mixed setup because the project is pointing to the Railway URL.

## 4. Start The Frontend

Open a second PowerShell window and run:

```powershell
cd "C:\Users\safsa\Desktop\New folder\cvservice\frontend"
python -m http.server 5173 --bind 127.0.0.1
```

Then open:

```txt
http://127.0.0.1:5173/login.html
```

You can also use:

- `http://127.0.0.1:5173/register.html`
- `http://127.0.0.1:5173/verify-email.html`

## 5. Test The Main Flow

Use this order:

1. register a user through the local auth service
2. verify the email if your auth flow requires it
3. log in
4. open the dashboard
5. create a job
6. upload a CV
7. wait for scoring to complete

## 6. What Should Work In This Setup

If the current mixed setup is healthy:

- login and profile use local auth
- job creation goes to Railway `job_service`
- CV upload goes to local `cv_service`
- local `ai_worker` fetches job details from Railway
- scoring results come back into local `cv_service`

## 7. Useful Endpoints

- Auth health:
  - `http://127.0.0.1:8001/api/auth/health/`
- CV API base:
  - `http://127.0.0.1:8000/api`
- Railway job API base:
  - `https://romantic-commitment-production.up.railway.app/api`
- RabbitMQ dashboard:
  - `http://127.0.0.1:15672`

## 8. Common Problems

### Login works but dashboard requests fail

Usually means one of these:

- local services are not fully started yet
- Railway `job_service` is unavailable
- browser still has an old token

Fix:

- wait for Docker services to finish starting
- clear browser storage:

```js
localStorage.clear()
```

### `Given token not valid for any token type`

Cause:

- `JWT_SIGNING_KEY` mismatch between local auth, Railway job service, and local CV service

Expected shared value in this repo:

```txt
shared-jwt-signing-key
```

### CV upload works but scoring does not finish

Cause:

- `ai_worker` cannot reach RabbitMQ
- `ai_worker` cannot reach the Railway job service
- `INTERNAL_API_TOKEN` mismatch

Expected shared internal token:

```txt
shared-internal-service-token
```

### Old data or strange test results

Cause:

- previous test data still exists in SQLite or media files

If needed, wipe local test data before rerunning.

## 9. If You Want Fully Local Testing Instead

The current repo is not set to fully local job testing right now.

To switch back to fully local:

1. In `frontend/config.js`, change:

```txt
JOB_API_BASE=http://127.0.0.1:8002/api
```

2. In `deploy/docker-compose.yml`, change both `JOB_SERVICE_URL` values back to:

```txt
http://job_service:8000
```

3. Restart the stack:

```powershell
cd "C:\Users\safsa\Desktop\New folder\cvservice\deploy"
docker compose down
docker compose up --build
```

## 10. Success Check

The system is working when all of these are true:

- you can log in from the frontend
- dashboard loads without auth errors
- creating a job succeeds
- uploading a CV succeeds
- the uploaded CV changes from processing to scored
