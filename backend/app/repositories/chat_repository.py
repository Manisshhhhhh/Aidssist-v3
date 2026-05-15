from __future__ import annotations

import json
from typing import Any

from app.db.models import ChatConversation, ChatMessage
from app.db.session import new_session
from app.models.chat_models import ChatResponse


def save_chat_exchange(response: ChatResponse) -> None:
    session = new_session()
    try:
        conversation = (
            session.query(ChatConversation)
            .filter(ChatConversation.conversation_id == response.conversation_id)
            .one_or_none()
        )
        if conversation is None:
            conversation = ChatConversation(
                conversation_id=response.conversation_id,
                dataset_id=response.dataset_id,
            )
            session.add(conversation)

        session.add(
            ChatMessage(
                conversation_id=response.conversation_id,
                role="user",
                message=response.message,
            )
        )
        session.add(
            ChatMessage(
                conversation_id=response.conversation_id,
                role="assistant",
                message=response.answer,
                intent=response.intent,
                answer=response.answer,
                result_json=json.dumps(response.result.model_dump(mode="json")),
            )
        )
        session.commit()
    finally:
        session.close()


def latest_chat_exchanges(dataset_id: str, limit: int = 5) -> list[dict[str, Any]]:
    session = new_session()
    try:
        messages = (
            session.query(ChatMessage)
            .join(ChatConversation, ChatConversation.conversation_id == ChatMessage.conversation_id)
            .filter(ChatConversation.dataset_id == dataset_id)
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .limit(limit * 2)
            .all()
        )
        messages = list(reversed(messages))
        exchanges: list[dict[str, Any]] = []
        pending_user: str | None = None
        for message in messages:
            if message.role == "user":
                pending_user = message.message
            elif message.role == "assistant" and pending_user:
                exchanges.append(
                    {
                        "question": pending_user,
                        "answer": message.answer or message.message,
                        "intent": message.intent,
                    }
                )
                pending_user = None
        return exchanges[-limit:]
    finally:
        session.close()
