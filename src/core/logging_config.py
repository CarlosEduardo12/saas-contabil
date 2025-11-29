import logging
import re
from typing import Any

class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        # Mask JWT tokens
        msg = re.sub(r'Bearer\s+[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+', 'Bearer *****', msg)
        # Mask passwords (simple regex for demonstration)
        msg = re.sub(r'password=[\w@#$%^&+=]+', 'password=*****', msg)
        record.msg = msg
        return True

def configure_logging():
    logger = logging.getLogger("saas_contabil")
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Add filter
    handler.addFilter(SensitiveDataFilter())
    
    logger.addHandler(handler)
    return logger

logger = configure_logging()
