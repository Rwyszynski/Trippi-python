from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from database import get_db
from models import Conversation, ConversationParticipant, Message
from schemas import ConversationCreate, ConversationResponse, MessageCreate, MessageResponse
from auth import get_current_user_id

router = APIRouter(prefix="/v1/chat", tags=["chat"])


def build_conversation_response(conv: Conversation) -> ConversationResponse:
    participants = [p.user_id for p in conv.participants]
    last_message = conv.messages[-1] if conv.messages else None
    return ConversationResponse(
        id=conv.id,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        participants=participants,
        last_message=MessageResponse.model_validate(last_message) if last_message else None,
    )


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    data: ConversationCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    existing = (
        db.query(Conversation)
        .join(ConversationParticipant)
        .filter(ConversationParticipant.user_id == current_user_id)
        .all()
    )
    for conv in existing:
        participant_ids = {str(p.user_id) for p in conv.participants}
        if str(data.participant_id) in participant_ids and len(participant_ids) == 2:
            return build_conversation_response(conv)

    # Stwórz nową konwersację
    conversation = Conversation()
    db.add(conversation)
    db.flush()

    db.add(ConversationParticipant(conversation_id=conversation.id, user_id=current_user_id))
    db.add(ConversationParticipant(conversation_id=conversation.id, user_id=data.participant_id))
    db.commit()
    db.refresh(conversation)

    return build_conversation_response(conversation)


@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    conversations = (
        db.query(Conversation)
        .join(ConversationParticipant)
        .filter(ConversationParticipant.user_id == current_user_id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return [build_conversation_response(c) for c in conversations]


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Konwersacja nie znaleziona")

    participant_ids = {str(p.user_id) for p in conv.participants}
    if current_user_id not in participant_ids:
        raise HTTPException(status_code=403, detail="Brak dostępu do tej konwersacji")

    return build_conversation_response(conv)

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_messages(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Konwersacja nie znaleziona")

    participant_ids = {str(p.user_id) for p in conv.participants}
    if current_user_id not in participant_ids:
        raise HTTPException(status_code=403, detail="Brak dostępu")

    # Oznacz wiadomości jako przeczytane
    db.query(Message).filter(
        Message.conversation_id == conversation_id,
        Message.sender_id != current_user_id,
        Message.read == False,
    ).update({"read": True})
    db.commit()

    return conv.messages


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    conversation_id: UUID,
    data: MessageCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Konwersacja nie znaleziona")

    participant_ids = {str(p.user_id) for p in conv.participants}
    if current_user_id not in participant_ids:
        raise HTTPException(status_code=403, detail="Brak dostępu")

    message = Message(
        conversation_id=conversation_id,
        sender_id=current_user_id,
        content=data.content,
    )
    db.add(message)

    from datetime import datetime, timezone
    conv.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(message)

    return message

@router.delete("/conversations/{conversation_id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    conversation_id: UUID,
    message_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.conversation_id == conversation_id,
    ).first()

    if not message:
        raise HTTPException(status_code=404, detail="Wiadomość nie znaleziona")
    if str(message.sender_id) != current_user_id:
        raise HTTPException(status_code=403, detail="Możesz usuwać tylko własne wiadomości")

    db.delete(message)
    db.commit()