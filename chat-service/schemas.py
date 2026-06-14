from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class ConversationCreate(BaseModel):
    participant_id: UUID


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_id: UUID
    content: str
    read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    participants: List[UUID]
    last_message: Optional[MessageResponse] = None

    class Config:
        from_attributes = True