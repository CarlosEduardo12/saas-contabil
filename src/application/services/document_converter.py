from pathlib import Path
from domain.ports.document_reader import DocumentReader
from domain.ports.document_writer import DocumentWriter


class DocumentConverterService:
    """Serviço de conversão de documentos."""

    def __init__(self, reader: DocumentReader, writer: DocumentWriter):
        self.reader = reader
        self.writer = writer

    def convert(self, input_path: Path, output_path: Path) -> None:
        """Converte um documento do formato de entrada para o formato de saída."""
        document = self.reader.read(input_path)
        self.writer.write(document, output_path)
