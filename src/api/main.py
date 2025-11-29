from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
import shutil
from pathlib import Path
import os
from celery.result import AsyncResult

from src.core.celery_app import celery_app
from src.core.config import settings
from src.services.validator import PDFValidatorService
from src.worker.tasks import convert_document_task
from src.api.schemas import TaskResponse, ConversionResult

app = FastAPI(title=settings.PROJECT_NAME)

validator_service = PDFValidatorService()


@app.post("/convert", response_model=TaskResponse)
async def convert_document(file: UploadFile = File(...)):
    # Salvar arquivo temporariamente
    file_path = Path(settings.UPLOAD_DIR) / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Validar
    if not validator_service.validate(file_path):
        os.remove(file_path)
        raise HTTPException(status_code=404, detail="PDF não cadastrado na base.")

    # Disparar tarefa
    task = convert_document_task.delay(str(file_path))

    return TaskResponse(task_id=task.id, status="processing")


@app.get("/result/{task_id}")
async def get_result(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.state == "PENDING":
        return {"task_id": task_id, "status": "processing"}
    elif task_result.state == "FAILURE":
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(task_result.result),
        }
    elif task_result.state == "SUCCESS":
        result_data = task_result.result
        if result_data.get("status") == "error":
            return {
                "task_id": task_id,
                "status": "failed",
                "error": result_data.get("error"),
            }

        output_path = result_data.get("output_path")
        if output_path and os.path.exists(output_path):
            return FileResponse(
                path=output_path,
                filename=result_data.get("filename"),
                media_type="text/csv",
            )
        else:
            return {
                "task_id": task_id,
                "status": "failed",
                "error": "Output file not found",
            }

    return {"task_id": task_id, "status": task_result.state}
