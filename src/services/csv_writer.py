import csv
from datetime import datetime
from pathlib import Path
import re

from src.domain.entities import Document, DocumentWriteError


class CSVWriter:
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
        month, year = self.extract_month_year(text)
        if not month or not year:
            raise DocumentWriteError("Não foi possível encontrar mês e ano no texto")

        return self._extract_time_entries(text, month, year)

    def _extract_time_entries(
        self, text: str, month: str, year: str
    ) -> list[list[str]]:
        """Extrai registros de ponto do texto com mês e ano conhecidos."""
        line_pattern = r"(\d{2})\s+((?:\d{2}:\d{2}/\d{2}:\d{2}\s*){1,4})\s+(\d{2}:\d{2})(?:\s+(.+?))?$"
        time_pattern = r"(\d{2}:\d{2}/\d{2}:\d{2})"

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

    def parse_s15_time_entries(self, text: str) -> list[list[str]]:
        """
        Processa o texto para extrair registros de ponto no formato S15 GP SERVIÇOS GERAIS.
        Ignora dias com FOLGA.
        """
        records = []

        # Captura qualquer linha com data no formato DD/MM/AAAA seguida de 4 horários no formato HH:MM
        date_pattern = r"(\d{2}/\d{2}/\d{4})"
        time_pattern = r"(\d{2}:\d{2})"

        for line in text.split("\n"):
            # Pula linhas com FOLGA
            if "FOLGA" in line:
                continue

            # Procura por uma data no formato DD/MM/AAAA na linha
            date_match = re.search(date_pattern, line)
            if date_match:
                date = date_match.group(1)

                # Procura por todos os horários no formato HH:MM na linha
                times = re.findall(time_pattern, line)

                # Se encontrou pelo menos 4 horários, usa-os como entrada1, saída1, entrada2, saída2
                if len(times) >= 4:
                    entries_exits = times[:4]  # Pega os primeiros 4 horários

                    # Completa com campos vazios até ter 12 campos
                    while len(entries_exits) < 12:
                        entries_exits.append("")

                    record = [date] + entries_exits
                    records.append(record)

        return records

    def detect_document_type(self, text: str) -> str:
        """
        Detecta o tipo de documento baseado no conteúdo.
        """
        text_upper = text.upper()
        if any(
            marker in text_upper
            for marker in ["S15 GP", "ESPELHO DO CARTÃO DE PONTO", "SERVIÇOS GERAIS"]
        ):
            return "s15"
        return "default"

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
                # Detecta o tipo de documento e usa o parser apropriado
                doc_type = self.detect_document_type(page.content)

                try:
                    if doc_type == "s15":
                        records = self.parse_s15_time_entries(page.content)
                    else:
                        records = self.parse_time_entries(page.content)

                    all_records.extend(records)
                except DocumentWriteError as e:
                    # Se houver erro em uma página, registre o erro e continue com as próximas
                    print(f"Aviso: Erro ao processar uma página: {str(e)}")
                    continue

            if not all_records:
                raise DocumentWriteError(
                    "Não foi possível extrair registros de ponto de nenhuma página"
                )

            # Ordena os registros por data
            all_records.sort(key=lambda x: datetime.strptime(x[0], "%d/%m/%Y"))

            with open(output_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file, delimiter=";")
                writer.writerow(headers)
                writer.writerows(all_records)

        except Exception as e:
            raise DocumentWriteError(f"Erro ao escrever arquivo CSV: {str(e)}")
