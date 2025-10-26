from abc import ABC, abstractmethod
from pathlib import Path

from domain.models import Document


class DocumentReader(ABC):
    """Interface para leitores de documentos."""

    @abstractmethod
    def read(self, file_path: Path) -> Document:
        """Lê um documento do caminho especificado."""
        pass
