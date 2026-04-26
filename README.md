# CV Service Monorepo

This repository contains the services that make up the CV platform.

## Services

- `auth-service-django-main/` - authentication service
- `cv_service/` - main CV service and local Docker Compose setup
- `job-ser-main/` - job management service
- `smart-cv-matcher-main/` - AI matching worker
- `notificatio_service/` - notification consumer

## Notes

- Local virtual environments, SQLite databases, media files, and `.env` files are excluded from Git.
- The Docker Compose file is located at `cv_service/docker-compose.yml`.
- Create your own local `.env` files before running the project.
