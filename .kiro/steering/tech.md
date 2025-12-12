# Technology Stack

## Backend Framework
- **FastAPI**: Modern Python web framework for building APIs
- **Python 3.11**: Runtime environment

## Database & Storage
- **PostgreSQL**: Primary database with AsyncPG driver
- **SQLAlchemy**: ORM with async support
- **Redis**: Message broker and caching

## Task Processing
- **Celery**: Distributed task queue for background processing
- **Redis**: Celery broker backend

## Authentication & Security
- **JWT (python-jose)**: Token-based authentication
- **Passlib with bcrypt**: Password hashing
- **OAuth2PasswordRequestForm**: FastAPI security integration

## Document Processing
- **PyPDF2**: PDF reading and text extraction
- **Custom CSV writer**: Structured data output

## External Integrations
- **Telegram Bot API**: Bot interface and payment processing
- **HTTPX**: HTTP client for external API calls

## Containerization
- **Docker**: Application containerization
- **Docker Compose**: Multi-service orchestration

## Development Tools
- **Uvicorn**: ASGI server for development and production

## Common Commands

### Development
```bash
# Start all services
docker-compose up

# Start only dependencies (Redis, PostgreSQL)
docker-compose up redis postgres

# Run API server locally
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Run Celery worker locally
celery -A src.core.celery_app.celery_app worker --loglevel=info
```

### Testing
```bash
# Run tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_api.py
```

### Database
```bash
# Access PostgreSQL container
docker-compose exec postgres psql -U postgres -d saas_contabil
```

### Verification Scripts
```bash
# Verify Docker setup
python verify_docker.py

# Verify security configuration
python verify_security.py

# Verify Telegram integration
python verify_telegram.py
```