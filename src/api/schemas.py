from pydantic import BaseModel
from typing import Optional

class TaskResponse(BaseModel):
    task_id: str
    status: str

class ConversionResult(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
