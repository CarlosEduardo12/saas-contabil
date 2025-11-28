from pathlib import Path
from typing import Any, Dict, Optional
import PyPDF2
import cv2
import numpy as np
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

from models import Document, Page, DocumentReadError


class PDFReader:
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
