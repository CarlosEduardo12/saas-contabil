import os

class Settings:
    PROJECT_NAME: str = "SaaS Contabil Converter"
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    UPLOAD_DIR: str = os.path.join(os.getcwd(), "uploads")
    OUTPUT_DIR: str = os.path.join(os.getcwd(), "outputs")

settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
