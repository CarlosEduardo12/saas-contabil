from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
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

app = FastAPI(title=settings.PROJECT_NAME)

validator_service = PDFValidatorService()

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # In a real app, verify against DB. Here we use a dummy check.
    if form_data.username != "admin" or form_data.password != "secret":
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
    logger.info(f"User {current_user} requested conversion for file: {file.filename}")
    # Salvar arquivo temporariamente
    file_path = Path(settings.UPLOAD_DIR) / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

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
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(task_result.result),
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
