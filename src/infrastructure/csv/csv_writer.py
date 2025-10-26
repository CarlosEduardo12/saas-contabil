import csv
from datetime import datetime
from pathlib import Path
import re
from domain.exceptions import DocumentWriteError
from domain.models import Document
from domain.ports.document_writer import DocumentWriter


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
