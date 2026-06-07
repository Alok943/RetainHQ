from pydantic import BaseModel
import uuid
from datetime import datetime

class FeedbackCreate(BaseModel):
    message: str

class FeedbackOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    message: str
    status: str
    created_at: datetime
