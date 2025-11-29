from pathlib import Path
import os

from src.core.celery_app import celery_app
from src.core.config import settings
from src.services.document_converter import DocumentConverterService
from src.services.pdf_reader import PDFReader
from src.services.csv_writer import CSVWriter

@celery_app.task(bind=True, name="convert_document")
def convert_document_task(self, input_path_str: str):
    try:
        input_path = Path(input_path_str)
        output_filename = input_path.stem + ".csv"
        output_path = Path(settings.OUTPUT_DIR) / output_filename
        
        # Instanciar serviços
        pdf_reader = PDFReader()
        csv_writer = CSVWriter()
        converter = DocumentConverterService(pdf_reader, csv_writer)
        
        # Converter
        converter.convert(input_path, output_path)
        
        return {
            "status": "success",
            "output_path": str(output_path),
            "filename": output_filename
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
