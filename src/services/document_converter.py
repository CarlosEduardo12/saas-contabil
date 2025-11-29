from pathlib import Path
from typing import Protocol

from src.domain.entities import Document


# Definindo protocolos implícitos para tipagem, se desejado, ou apenas usando duck typing.
# Para manter simples e parecido com o original, mas sem ports explícitos em arquivos separados.

class DocumentReader(Protocol):
    def read(self, file_path: Path) -> Document:
        ...

class DocumentWriter(Protocol):
    def write(self, document: Document, output_path: Path) -> None:
        ...


class DocumentConverterService:
    """Serviço de conversão de documentos."""

    def __init__(self, reader: DocumentReader, writer: DocumentWriter):
        self.reader = reader
        self.writer = writer

    def convert(self, input_path: Path, output_path: Path) -> None:
        """Converte um documento do formato de entrada para o formato de saída."""
        document = self.reader.read(input_path)
        self.writer.write(document, output_path)
