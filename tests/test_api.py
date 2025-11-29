import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

# Adicionar src ao path para importar módulos
sys.path.append(os.path.join(os.getcwd(), "src"))

from src.api.main import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("src.api.main.convert_document_task.delay")
    def test_convert_valid_pdf(self, mock_delay):
        mock_task = MagicMock()
        mock_task.id = "12345"
        mock_delay.return_value = mock_task

        # Criar um arquivo dummy
        filename = "PontoTest.pdf"
        content = b"%PDF-1.4..."
        
        files = {"file": (filename, content, "application/pdf")}
        response = self.client.post("/convert", files=files)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"task_id": "12345", "status": "processing"})
        mock_delay.assert_called_once()

    def test_convert_invalid_pdf(self):
        # Arquivo com nome inválido (não começa com Ponto)
        filename = "Invalid.pdf"
        content = b"%PDF-1.4..."
        
        files = {"file": (filename, content, "application/pdf")}
        response = self.client.post("/convert", files=files)
        
        self.assertEqual(response.status_code, 404)
        self.assertIn("PDF não cadastrado", response.json()["detail"])

    @patch("src.api.main.AsyncResult")
    def test_get_result_pending(self, mock_async_result):
        mock_result = MagicMock()
        mock_result.state = "PENDING"
        mock_async_result.return_value = mock_result
        
        response = self.client.get("/result/12345")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"task_id": "12345", "status": "processing"})

    @patch("api.main.AsyncResult")
    def test_get_result_success(self, mock_async_result):
        mock_result = MagicMock()
        mock_result.state = "SUCCESS"
        mock_result.result = {
            "status": "success",
            "output_path": "/tmp/output.csv",
            "filename": "output.csv"
        }
        mock_async_result.return_value = mock_result
        
        # Mock os.path.exists para retornar True
        with patch("os.path.exists", return_value=True):
            # Mock FileResponse para não tentar abrir o arquivo real
            with patch("src.api.main.FileResponse") as mock_file_response:
                mock_file_response.return_value = "FileResponseObject"
                response = self.client.get("/result/12345")
                # TestClient não lida bem com retorno de objeto mockado que não é Response, 
                # mas se passar pelo endpoint sem erro, é um bom sinal.
                # No entanto, o TestClient vai tentar ler a resposta.
                # Vamos verificar se chamou FileResponse corretamente.
                mock_file_response.assert_called_with(
                    path="/tmp/output.csv", 
                    filename="output.csv", 
                    media_type='text/csv'
                )

if __name__ == "__main__":
    unittest.main()
