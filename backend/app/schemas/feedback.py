from pydantic import BaseModel, ConfigDict, Field
import uuid
from datetime import datetime

class FeedbackCreate(BaseModel):
    message: str = Field(max_length=5000)

class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    message: str
    status: str
    created_at: datetime
