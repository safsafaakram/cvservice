# CV Service Monorepo

This repository contains the services that make up the CV platform.

## Services

- `auth-service-django-main/` - authentication service
- `cv_service/` - main CV service
- `job-ser-main/` - job management service
- `smart-cv-matcher-main/` - AI matching worker
- `notificatio_service/` - notification consumer
- `frontend/` - static frontend files
- `deploy/` - local Docker Compose and deployment-oriented files

## Notes

- Local virtual environments, SQLite databases, media files, and `.env` files are excluded from Git.
- The Docker Compose file is located at `deploy/docker-compose.yml`.
- Create your own local `.env` files before running the project.
