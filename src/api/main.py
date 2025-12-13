from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import shutil
from pathlib import Path
import os
from celery.result import AsyncResult
from datetime import timedelta

from src.core.celery_app import celery_app
from src.core.config import settings
from src.services.validator import PDFValidatorService
from src.worker.tasks import convert_document_task
from src.api.schemas import TaskResponse, ConversionResult, Token
from src.core.security import create_access_token, get_current_user
from src.core.logging_config import logger
from src.api.telegram import router as telegram_router
from src.core.database import engine, Base

app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/docs" if os.getenv("ENVIRONMENT") == "development" else None,  # SECURITY: Hide docs in production
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") == "development" else None
)

# SECURITY: Configure CORS properly (mais permissivo para desenvolvimento)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permissivo para desenvolvimento
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telegram_router)

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    health_status = {
        "status": "healthy",
        "service": "saas-contabil-converter",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "checks": {
            "secret_key": bool(settings.SECRET_KEY),
            "telegram_token": bool(settings.TELEGRAM_BOT_TOKEN),
            "database_url": bool(settings.DATABASE_URL)
        }
    }
    return health_status

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SaaS Contabil Converter API", 
        "status": "running",
        "version": "1.0.0",
        "timestamp": "2025-12-11"
    }











@app.on_event("startup")
async def startup():
    print("🚀 Starting SaaS Contabil Converter...")
    print(f"📊 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🔑 SECRET_KEY configured: {'Yes' if settings.SECRET_KEY else 'No'}")
    print(f"🤖 TELEGRAM_BOT_TOKEN configured: {'Yes' if settings.TELEGRAM_BOT_TOKEN else 'No'}")
    print(f"🗄️ DATABASE_URL: {settings.DATABASE_URL[:50]}...")
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Database error: {e}")
        # Don't exit, let the app start anyway for health check

validator_service = PDFValidatorService()

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # SECURITY: Use environment variables for credentials
    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")
    
    if not admin_username or not admin_password:
        logger.error("Admin credentials not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error"
        )
    
    # SECURITY: Use constant-time comparison to prevent timing attacks
    from secrets import compare_digest
    username_valid = compare_digest(form_data.username, admin_username)
    password_valid = compare_digest(form_data.password, admin_password)
    
    if not (username_valid and password_valid):
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    logger.info(f"User {form_data.username} logged in successfully")
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/convert", response_model=TaskResponse)
async def convert_document(
    file: UploadFile = File(...), 
    current_user: str = Depends(get_current_user)
):
    # SECURITY: Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    # SECURITY: Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed")
    
    # SECURITY: Check file size
    if file.size and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE // (1024*1024)} MB")
    
    # SECURITY: Sanitize filename to prevent path traversal
    import re
    safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', file.filename)
    safe_filename = safe_filename[:100]  # Limit filename length
    
    # SECURITY: Use UUID for unique filename
    import uuid
    unique_filename = f"{uuid.uuid4()}_{safe_filename}"
    file_path = Path(settings.UPLOAD_DIR) / unique_filename
    
    logger.info(f"User {current_user} requested conversion for file: {safe_filename}")
    
    # SECURITY: Limit file content size during write
    max_size = settings.MAX_FILE_SIZE
    total_size = 0
    
    with open(file_path, "wb") as buffer:
        while chunk := await file.read(8192):  # Read in chunks
            total_size += len(chunk)
            if total_size > max_size:
                buffer.close()
                os.remove(file_path)
                raise HTTPException(status_code=400, detail="File too large")
            buffer.write(chunk)

    # Validar
    if not validator_service.validate(file_path):
        logger.warning(f"Validation failed for file: {file.filename}")
        os.remove(file_path)
        raise HTTPException(status_code=404, detail="PDF não cadastrado na base.")

    # Disparar tarefa
    task = convert_document_task.delay(str(file_path))
    logger.info(f"Task {task.id} started for file: {file.filename}")

    return TaskResponse(task_id=task.id, status="processing")


@app.get("/result/{task_id}")
async def get_result(
    task_id: str,
    current_user: str = Depends(get_current_user)
):
    logger.info(f"User {current_user} checked result for task: {task_id}")
    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.state == "PENDING":
        return {"task_id": task_id, "status": "processing"}
    elif task_result.state == "FAILURE":
        logger.error(f"Task {task_id} failed: {task_result.result}")
        # SECURITY: Don't expose internal error details
        return {
            "task_id": task_id,
            "status": "failed",
            "error": "Processing failed. Please try again or contact support.",
        }
    elif task_result.state == "SUCCESS":
        result_data = task_result.result
        if result_data.get("status") == "error":
            logger.error(f"Task {task_id} returned error: {result_data.get('error')}")
            return {
                "task_id": task_id,
                "status": "failed",
                "error": result_data.get("error"),
            }

        output_path = result_data.get("output_path")
        if output_path and os.path.exists(output_path):
            logger.info(f"Task {task_id} success. Returning file.")
            return FileResponse(
                path=output_path,
                filename=result_data.get("filename"),
                media_type="text/csv",
            )
        else:
            logger.error(f"Task {task_id} success but output file missing: {output_path}")
            return {
                "task_id": task_id,
                "status": "failed",
                "error": "Output file not found",
            }

    return {"task_id": task_id, "status": task_result.state}
