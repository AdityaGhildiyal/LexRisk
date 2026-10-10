from pydantic import BaseModel
from typing import Optional

class ContractUploadRequest(BaseModel):
    filename: str
    content_type: str
    file_size: int
    description: Optional[str] = None
