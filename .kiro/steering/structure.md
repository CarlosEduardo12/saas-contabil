# Project Structure

## Architecture Pattern
The project follows **Clean Architecture** principles with clear separation of concerns across layers.

## Directory Organization

### `/src` - Main Application Code
- **`/api`** - Web layer (FastAPI routes and schemas)
  - `main.py` - FastAPI application entry point and core endpoints
  - `telegram.py` - Telegram webhook handlers and bot integration
  - `schemas.py` - Pydantic models for request/response validation

- **`/core`** - Infrastructure and configuration
  - `config.py` - Application settings and environment variables
  - `database.py` - Database connection and session management
  - `security.py` - Authentication and JWT token handling
  - `celery_app.py` - Celery configuration and app instance
  - `logging_config.py` - Centralized logging setup

- **`/domain`** - Business entities and domain logic
  - `entities.py` - Core domain models (Document, Page) and exceptions
  - `__init__.py` - Domain layer initialization

- **`/models`** - Database models (SQLAlchemy)
  - `order.py` - Order and Payment database models

- **`/services`** - Application services and business logic
  - `pdf_reader.py` - PDF document reading implementation
  - `csv_writer.py` - CSV output generation
  - `document_converter.py` - Main conversion orchestration
  - `validator.py` - PDF validation against registered database
  - `telegram.py` - Telegram API service wrapper

- **`/worker`** - Background task processing
  - `tasks.py` - Celery task definitions for async processing

### `/tests` - Test Suite
- `test_api.py` - API endpoint tests

### `/uploads` - File Storage
- Temporary storage for uploaded PDF files

### `/outputs` - Generated Files
- Storage for converted CSV files

### Root Level Files
- `docker-compose.yml` - Multi-service container orchestration
- `Dockerfile` - Application container definition
- `requirements.txt` - Python dependencies
- `verify_*.py` - System verification scripts

## Naming Conventions

### Files and Directories
- Use snake_case for Python files and directories
- Service classes end with `Service` (e.g., `PDFValidatorService`)
- Model files use singular nouns (e.g., `order.py` not `orders.py`)

### Classes and Functions
- Classes use PascalCase (e.g., `DocumentConverter`)
- Functions and methods use snake_case (e.g., `convert_document`)
- Constants use UPPER_SNAKE_CASE (e.g., `PROJECT_NAME`)

### Database Models
- Table names use singular form
- Foreign key fields end with `_id`
- Use descriptive field names (e.g., `provider_payment_id`)

## Import Organization
1. Standard library imports
2. Third-party library imports
3. Local application imports (using absolute imports from `src`)

## Configuration Management
- All configuration in `src/core/config.py`
- Environment variables with sensible defaults
- Separate settings for different environments via environment variables