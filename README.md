# Delivery App API

A scalable, modular backend API for a delivery platform, built with **FastAPI**, **SQLAlchemy**, **Docker**, and supporting modern authentication, user roles, product management, and integrations with Redis and MinIO.

## Table of Contents

- [Delivery App API](#delivery-app-api)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Features](#features)
  - [Architecture \& Components](#architecture--components)
    - [Main Folders](#main-folders)
  - [API Modules](#api-modules)
  - [Setup \& Usage](#setup--usage)
    - [Prerequisites](#prerequisites)
    - [Running with Docker](#running-with-docker)
    - [Local Development](#local-development)
  - [Environment Variables](#environment-variables)
  - [Development \& Testing](#development--testing)
  - [License](#license)

---

## Overview

This project provides a backend API for a delivery service, supporting user registration, authentication, product and category management, company and driver onboarding, discounts, and more. It is designed for extensibility and production-readiness, using Docker for containerization and supporting cloud deployment.

---

## Features

- **User Authentication & Authorization**
  - JWT-based login, refresh, and revoke tokens
  - Role-based access (admin, company, driver, customer)
- **User Management**
  - Register and update customers, drivers, and companies
  - Profile management for each user type
- **Product & Category Management**
  - CRUD for products and categories
  - Product images upload (MinIO integration)
  - Discounts and promotions
- **Order & Discount System**
  - (Planned/extendable) endpoints for order management
  - Discount creation and application
- **Currency & GeoIP**
  - Currency exchange rates (with periodic updates)
  - GeoIP-based currency selection
- **Integrations**
  - PostgreSQL (database)
  - Redis (caching, token storage)
  - MinIO (object storage for images)
  - Docker Compose for orchestration
- **Health Checks & Monitoring**
  - `/health` endpoint for service status
  - Application logs and container status in CI

---

## Architecture & Components

- **FastAPI**: Main web framework for API endpoints.
- **SQLAlchemy**: ORM for database models and queries.
- **Alembic**: Database migrations.
- **Redis**: Caching and token storage.
- **MinIO**: S3-compatible object storage for file uploads.
- **Docker**: Containerization for all services.
- **Nginx**: (Optional) reverse proxy configuration.

### Main Folders

- `app/`
  - `api/`: Route definitions for users, products, companies, drivers, customers, categories, discounts.
  - `core/`: Business logic (CRUD operations, authentication, etc.).
  - `db/`: Database, Redis, and MinIO connection utilities.
  - `models/`: SQLAlchemy models for users, products, etc.
  - `schemas/`: Pydantic schemas for request/response validation.
  - `utils/`: Utility functions (security, currency, geolocation).
- `alembic/`: Database migration scripts.
- `scripts/`: Helper scripts for environment and setup.
- `collections/`: API test collections (e.g., for Bruno).
- `Dockerfile`, `compose.yaml`: Docker configuration.

---

## API Modules

- **/users**: Registration, login, token management, profile, file upload.
- **/companies**: Company registration and profile management.
- **/drivers**: Driver registration and profile management.
- **/customers**: Customer registration and profile management.
- **/products**: Product CRUD, image upload, discounts.
- **/categories**: Category CRUD.
- **/discounts**: Discount CRUD.
- **/health**: Health check endpoint.

---

## Setup & Usage

### Prerequisites

- Docker & Docker Compose
- (Optional) Python 3.13+ for local development

### Running with Docker

```bash
docker compose up --build
```

The API will be available at [http://localhost:8000](http://localhost:8000).

### Local Development

1. Create a virtual environment and install dependencies:

   ```bash
   python3.13 -m venv env
   source env/bin/activate
   pip install -r requirements.txt
   ```

2. Set up your `.env` file (see below).
3. Run the app:

   ```bash
   uvicorn main:app --reload
   ```

---

## Environment Variables

The app uses a `.env` file for configuration. Example variables:

- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT`
- `JWT_SECRET_KEY`, `JWT_ALGORITHM`
- `REDIS_HOST`, `REDIS_PORT`
- `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_ENDPOINT`, `MINIO_PORT`, `MINIO_BUCKET`
- `GEOIP_API_HOST`, `GEOIP_API_PORT`
- `EXCHANGE_API_ID`

---

## Development & Testing

- **Linting/formatting**: Use `black`, `flake8`, or your preferred tools.
- **Testing**: (Add your test strategy here, e.g., pytest, API test collections in `collections/`)
- **CI/CD**: See `.github/workflows/fast_api.yml` for GitHub Actions workflow.

---

## License

MIT License 

---