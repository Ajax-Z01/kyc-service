from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentCreate(BaseModel):
    wallet_address: str

class DocumentInDB(BaseModel):
    id: str
    wallet_address: str
    file_name: str
    file_hash: str
    status: str
    token_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

class DocumentResponse(BaseModel):
    id: str
    wallet_address: str
    file_name: str
    file_hash: str
    status: str
    token_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
