from dataclasses import dataclass
from typing import List


class DocumentProcessingError(Exception):
    """Exceção base para erros de processamento de documentos."""
    pass


class DocumentReadError(DocumentProcessingError):
    """Exceção para erros de leitura de documentos."""
    pass


class DocumentWriteError(DocumentProcessingError):
    """Exceção para erros de escrita de documentos."""
    pass


@dataclass(frozen=True)
class Page:
    """Representa uma página de documento com seu conteúdo e metadados."""
    content: str
    page_number: int


@dataclass(frozen=True)
class Document:
    """Representa um documento completo com suas páginas."""
    pages: List[Page]
    name: str
