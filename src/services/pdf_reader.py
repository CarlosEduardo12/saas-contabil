from pathlib import Path
import PyPDF2

from src.domain.entities import Document, Page, DocumentReadError


class PDFReader:
    """Implementação de leitor de documentos PDF."""

    def __init__(self):
        pass

    def read(self, file_path: Path) -> Document:
        """Lê um documento PDF e extrai seu conteúdo."""
        try:
            pages = []

            # Abrir PDF para leitura normal de texto
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)

                for page_num in range(len(pdf_reader.pages)):
                    # Extrair texto normalmente
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text().strip()

                    pages.append(
                        Page(
                            content=text,
                            page_number=page_num + 1,
                        )
                    )

            return Document(pages=pages, name=file_path.stem)

        except Exception as e:
            raise DocumentReadError(f"Erro ao ler arquivo PDF: {str(e)}")
