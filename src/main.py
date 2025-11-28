from pathlib import Path
from services.document_converter import DocumentConverterService
from models import DocumentProcessingError
from services.csv_writer import CSVWriter
from services.pdf_reader import PDFReader


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

        input_path = Path("Ponto4.pdf")
        document = pdf_reader.read(input_path)

        for page in document.pages:
            print(f"\n--- Página {page.page_number} ---\n")
            print(page.content)
        output_path = Path("output4.csv")

        converter.convert(input_path, output_path)
        print(f"Conversão concluída com sucesso: {input_path} -> {output_path}")

    except DocumentProcessingError as e:
        print(f"Erro de processamento: {str(e)}")
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")


if __name__ == "__main__":
    main()
