from typing import Annotated

from fastapi import Depends, Request

from app.api.deps import SessionDep
from app.db.session import session_factory

from .llm import ChatModel, ClaudeChatModel
from .repository import ChatRepository
from .service import ChatService


def get_chat_model(request: Request) -> ChatModel:
    # The AsyncAnthropic client is created once in the app lifespan and shared.
    return ClaudeChatModel(request.app.state.anthropic)


def get_chat_service(
    session: SessionDep, llm: Annotated[ChatModel, Depends(get_chat_model)]
) -> ChatService:
    return ChatService(ChatRepository(session), llm, session_factory())


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
