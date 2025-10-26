from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import csv
import PyPDF2
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import cv2
import numpy as np


# Domain Models
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


# Domain Exceptions
class DocumentProcessingError(Exception):
    """Exceção base para erros de processamento de documentos."""

    pass


class DocumentReadError(DocumentProcessingError):
    """Exceção para erros de leitura de documentos."""

    pass


class DocumentWriteError(DocumentProcessingError):
    """Exceção para erros de escrita de documentos."""

    pass


# Interfaces/Ports
class DocumentReader(ABC):
    """Interface para leitores de documentos."""

    @abstractmethod
    def read(self, file_path: Path) -> Document:
        """Lê um documento do caminho especificado."""
        pass


class DocumentWriter(ABC):
    """Interface para escritores de documentos."""

    @abstractmethod
    def write(self, document: Document, output_path: Path) -> None:
        """Escreve um documento no caminho especificado."""
        pass


# Infrastructure Layer
class PDFReader(DocumentReader):
    """Implementação de leitor de documentos PDF com suporte a OCR e pré-processamento de imagem."""

    def __init__(
        self,
        tesseract_path: Optional[str] = None,
        tesseract_config: Optional[Dict[str, Any]] = None,
        preprocessing_enabled: bool = True,
    ):
        self.tesseract_config = tesseract_config or {
            "lang": "por",
            # Configurações do OCR para melhorar reconhecimento
            "config": "--psm 3 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝàáâãäåçèéêëìíîïñòóôõöùúûüý0123456789.,:-/()[]{}@#$%&*<>!?+ ",
        }
        self.preprocessing_enabled = preprocessing_enabled
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def read(self, file_path: Path) -> Document:
        """Lê um documento PDF e extrai seu conteúdo."""
        try:
            pages = []
            # Converter PDF em imagens
            pdf_images = convert_from_path(file_path)

            # Abrir PDF para leitura normal de texto
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)

                for page_num in range(len(pdf_reader.pages)):
                    # Extrair texto normalmente
                    page = pdf_reader.pages[page_num]
                    direct_text = page.extract_text().strip()

                    # Extrair texto via OCR
                    image = pdf_images[page_num]
                    ocr_text = self._extract_ocr_text(image)

                    # Combinar os textos
                    combined_text = self._combine_texts(direct_text, ocr_text)

                    # Verificar se o conteúdo veio principalmente do OCR
                    is_image = len(direct_text) < len(ocr_text)

                    pages.append(
                        Page(
                            content=combined_text,
                            is_image=is_image,
                            page_number=page_num + 1,
                        )
                    )

            return Document(pages=pages, name=file_path.stem)

        except Exception as e:
            raise DocumentReadError(f"Erro ao ler arquivo PDF: {str(e)}")

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Aplica várias técnicas de pré-processamento para melhorar a qualidade da imagem."""
        # Converter para array numpy
        img_array = np.array(image)

        # Converter para escala de cinza se necessário
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Aplicar threshold adaptativo
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # Remover ruído
        denoised = cv2.fastNlMeansDenoising(binary)

        # Melhorar contraste
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # Aumentar resolução
        enhanced = cv2.resize(enhanced, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

        # Converter de volta para PIL Image
        return Image.fromarray(enhanced)

    def _extract_ocr_text(self, image: Image.Image) -> str:
        """Extrai texto via OCR da imagem com pré-processamento."""
        try:
            if self.preprocessing_enabled:
                # Aplicar pré-processamento
                processed_image = self._preprocess_image(image)

                # Tentar OCR com a imagem processada
                text = pytesseract.image_to_string(
                    processed_image, **self.tesseract_config
                ).strip()

                # Se o resultado for muito curto, tentar com a imagem original
                if len(text) < 50:  # valor arbitrário, ajuste conforme necessário
                    text_original = pytesseract.image_to_string(
                        image, **self.tesseract_config
                    ).strip()

                    # Usar o resultado mais longo
                    return text if len(text) > len(text_original) else text_original

                return text
            else:
                return pytesseract.image_to_string(
                    image, **self.tesseract_config
                ).strip()

        except Exception as e:
            print(f"Erro no OCR: {str(e)}")
            return ""

    def _combine_texts(self, direct_text: str, ocr_text: str) -> str:
        """Combina textos extraídos, usando heurísticas para escolher o melhor resultado."""

        def text_quality_score(text: str) -> float:
            """Calcula um score de qualidade para o texto baseado em heurísticas."""
            if not text:
                return 0.0

            # Proporção de caracteres alfanuméricos
            alnum_ratio = sum(c.isalnum() or c.isspace() for c in text) / len(text)

            # Presença de palavras comuns em português
            common_words = {
                "de",
                "da",
                "do",
                "em",
                "para",
                "com",
                "os",
                "as",
                "no",
                "na",
            }
            word_count = sum(word.lower() in common_words for word in text.split())

            # Calcular score final
            return (alnum_ratio * 0.7) + (word_count * 0.3)

        # Calcular scores
        direct_score = text_quality_score(direct_text)
        ocr_score = text_quality_score(ocr_text)

        # Escolher o texto com melhor score
        if direct_score > ocr_score:
            return direct_text
        elif ocr_score > direct_score:
            return ocr_text
        else:
            # Se os scores forem iguais, usar o mais longo
            return direct_text if len(direct_text) > len(ocr_text) else ocr_text


class CSVWriter(DocumentWriter):
    """Implementação de escritor de documentos em formato CSV para dados de ponto."""

    def __init__(self):
        self.month_map = {
            "JANEIRO": "01",
            "FEVEREIRO": "02",
            "MARÇO": "03",
            "ABRIL": "04",
            "MAIO": "05",
            "JUNHO": "06",
            "JULHO": "07",
            "AGOSTO": "08",
            "SETEMBRO": "09",
            "OUTUBRO": "10",
            "NOVEMBRO": "11",
            "DEZEMBRO": "12",
        }

    def extract_month_year(self, text: str) -> tuple[str, str]:
        """Extrai mês e ano do texto usando regex."""
        pattern = r"([A-Z][A-Za-zÇç]+)\s*/\s*(\d{4})"
        match = re.search(pattern, text)
        if match:
            month_name, year = match.groups()
            month_number = self.month_map.get(month_name.upper())
            if month_number:
                return month_number, year
        return None, None

    def parse_time_entries(self, text: str) -> list[list[str]]:
        """Processa o texto para extrair os registros de ponto."""
        line_pattern = r"(\d{2})\s+((?:\d{2}:\d{2}/\d{2}:\d{2}\s*){1,4})\s+(\d{2}:\d{2})(?:\s+(.+?))?$"
        time_pattern = r"(\d{2}:\d{2}/\d{2}:\d{2})"

        month, year = self.extract_month_year(text)
        if not month or not year:
            raise DocumentWriteError("Não foi possível encontrar mês e ano no texto")

        records = []

        for line in text.split("\n"):
            match = re.search(line_pattern, line.strip())
            if match:
                day = match.group(1)
                time_pairs = match.group(2).strip()

                times = re.findall(time_pattern, time_pairs)
                entries_exits = []
                for pair in times:
                    entry, exit = pair.split("/")
                    entries_exits.extend([entry, exit])

                while len(entries_exits) < 12:
                    entries_exits.append("")

                date = f"{day}/{month}/{year}"
                record = [date] + entries_exits
                records.append(record)

        return records

    def write(self, document: Document, output_path: Path) -> None:
        """Escreve os dados de ponto em formato CSV."""
        try:
            headers = [
                "Data",
                "Entrada 1",
                "Saida 1",
                "Entrada 2",
                "Saida 2",
                "Entrada 3",
                "Saida 3",
                "Entrada 4",
                "Saida 4",
                "Entrada 5",
                "Saida 5",
                "Entrada 6",
                "Saida 6",
            ]

            # Processa todas as páginas do documento
            all_records = []
            for page in document.pages:
                records = self.parse_time_entries(page.content)
                all_records.extend(records)

            # Ordena os registros por data
            all_records.sort(key=lambda x: datetime.strptime(x[0], "%d/%m/%Y"))

            with open(output_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file, delimiter=";")
                writer.writerow(headers)
                writer.writerows(all_records)

        except Exception as e:
            raise DocumentWriteError(f"Erro ao escrever arquivo CSV: {str(e)}")


# Application Service
class DocumentConverterService:
    """Serviço de conversão de documentos."""

    def __init__(self, reader: DocumentReader, writer: DocumentWriter):
        self.reader = reader
        self.writer = writer

    def convert(self, input_path: Path, output_path: Path) -> None:
        """Converte um documento do formato de entrada para o formato de saída."""
        document = self.reader.read(input_path)
        self.writer.write(document, output_path)


def main():
    try:
        tesseract_config = {
            "lang": "por",
            "config": "--psm 3 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝàáâãäåçèéêëìíîïñòóôõöùúûüý0123456789.,:-/()[]{}@#$%&*<>!?+ ",
        }

        tesseract_path = "/opt/homebrew/bin/tesseract"

        pdf_reader = PDFReader(
            tesseract_path=tesseract_path,
            tesseract_config=tesseract_config,
            preprocessing_enabled=True,  # Habilita o pré-processamento de imagem
        )

        csv_writer = CSVWriter()
        converter = DocumentConverterService(pdf_reader, csv_writer)

        input_path = Path("input.pdf")
        output_path = Path("output.csv")

        converter.convert(input_path, output_path)
        print(f"Conversão concluída com sucesso: {input_path} -> {output_path}")

    except DocumentProcessingError as e:
        print(f"Erro de processamento: {str(e)}")
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")


if __name__ == "__main__":
    main()
