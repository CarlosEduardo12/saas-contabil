from pathlib import Path
import hashlib

class PDFValidatorService:
    """Serviço para validar se o PDF pode ser processado."""

    def __init__(self):
        # Em um cenário real, isso viria de um banco de dados
        self.allowed_hashes = set()
        # Mocking some allowed files for testing if needed, 
        # but for now we will allow any file if we don't enforce strict checking
        # or we can implement a "registration" method.
        
        # Para o MVP, vamos simular que todos os arquivos são válidos 
        # ou podemos adicionar um hash específico para teste.
        pass

    def calculate_hash(self, file_path: Path) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def validate(self, file_path: Path) -> bool:
        """
        Valida se o arquivo está cadastrado e é seguro.
        Retorna True se válido, False caso contrário.
        """
        try:
            # SECURITY: Check if file exists and is readable
            if not file_path.exists() or not file_path.is_file():
                return False
            
            # SECURITY: Check file size
            if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB limit
                return False
            
            # SECURITY: Basic PDF validation - check magic bytes
            with open(file_path, 'rb') as f:
                header = f.read(4)
                if header != b'%PDF':
                    return False
            
            # SECURITY: Calculate hash for validation
            file_hash = self.calculate_hash(file_path)
            
            # BUSINESS LOGIC: Check if file is registered
            # For now, allow files that start with "Ponto" or have specific hashes
            if file_path.name.startswith("Ponto"):
                return True
            
            # TODO: Implement proper database lookup for registered hashes
            # return file_hash in self.get_allowed_hashes_from_db()
            
            return False
            
        except Exception as e:
            # SECURITY: Log validation errors but don't expose details
            print(f"Validation error: {e}")
            return False
