from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Page:
    """Representa uma página de documento com seu conteúdo e metadados."""

    content: str
    is_image: bool
    page_number: int


@dataclass(frozen=True)
class Document:
    """Representa um documento completo com suas páginas."""

    pages: List[Page]
    name: str
