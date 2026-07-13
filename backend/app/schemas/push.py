from pydantic import BaseModel, Field


class VapidPublicKeyOut(BaseModel):
    key: str


class PushSubscribeIn(BaseModel):
    endpoint: str = Field(min_length=1, max_length=2000)
    p256dh: str = Field(min_length=1, max_length=500)
    auth: str = Field(min_length=1, max_length=500)
    userAgent: str | None = Field(default=None, max_length=500)
