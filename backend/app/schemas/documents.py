from __future__ import annotations

import uuid
from typing import Optional
from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    document_type: str
    file_name: str
    mime_type: str
    file_size: int
    is_default: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class SetDefaultRequest(BaseModel):
    pass  # no body needed — the doc id is in the path
