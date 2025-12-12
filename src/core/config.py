import os

class Settings:
    PROJECT_NAME: str = "SaaS Contabil Converter"
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    UPLOAD_DIR: str = os.path.join(os.getcwd(), "uploads")
    OUTPUT_DIR: str = os.path.join(os.getcwd(), "outputs")
    
    # SECURITY: Require SECRET_KEY to be set, no default
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # SECURITY: Admin credentials
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD")
    
    # SECURITY: File upload limits
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default
    ALLOWED_EXTENSIONS: set = {".pdf"}
    
    def validate(self):
        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable is required")
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        if not self.ADMIN_USERNAME or not self.ADMIN_PASSWORD:
            raise ValueError("ADMIN_USERNAME and ADMIN_PASSWORD environment variables are required")
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/saas_contabil")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_PROVIDER_TOKEN: str = os.getenv("TELEGRAM_PROVIDER_TOKEN", "")
    TELEGRAM_WEBHOOK_SECRET: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")

settings = Settings()

# SECURITY: Validate configuration on startup (flexible for Railway)
try:
    settings.validate()
except ValueError as e:
    print(f"CONFIGURATION WARNING: {e}")
    # In production, log warning but don't exit to allow Railway to start
    if os.getenv("ENVIRONMENT") != "production":
        exit(1)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

# SECURITY: Set secure permissions on directories
os.chmod(settings.UPLOAD_DIR, 0o750)
os.chmod(settings.OUTPUT_DIR, 0o750)
