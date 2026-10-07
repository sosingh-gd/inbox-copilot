from typing import Annotated

from fastapi import Depends, Request

from app.api.deps import SessionDep
from app.db.session import session_factory

from .llm import ClaudeFactExtractor
from .repository import MemoryRepository
from .service import MemoryService


def get_memory_service(request: Request, session: SessionDep) -> MemoryService:
    # The AsyncAnthropic client is created once in the app lifespan.
    extractor = ClaudeFactExtractor(request.app.state.anthropic)
    return MemoryService(MemoryRepository(session), extractor, session_factory())


MemoryServiceDep = Annotated[MemoryService, Depends(get_memory_service)]
