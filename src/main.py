from pathlib import Path
from services.document_converter import DocumentConverterService
from models import DocumentProcessingError
from services.csv_writer import CSVWriter
from services.pdf_reader import PDFReader


def main():
    try:
        pdf_reader = PDFReader()

        csv_writer = CSVWriter()
        converter = DocumentConverterService(pdf_reader, csv_writer)

        input_path = Path("Ponto1.pdf")
        output_path = Path("output1.csv")

        converter.convert(input_path, output_path)
        print(f"Conversão concluída com sucesso: {input_path} -> {output_path}")

    except DocumentProcessingError as e:
        print(f"Erro de processamento: {str(e)}")
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")


if __name__ == "__main__":
    main()
