from abc import ABC, abstractmethod
from pathlib import Path
from domain.models import Document


class DocumentWriter(ABC):
    """Interface para escritores de documentos."""

    @abstractmethod
    def write(self, document: Document, output_path: Path) -> None:
        """Escreve um documento no caminho especificado."""
        pass
