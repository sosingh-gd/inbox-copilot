from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field

from app.core.schemas import ApiModel


class FactCategory(StrEnum):
    preference = "preference"
    person = "person"
    commitment = "commitment"
    deadline = "deadline"
    other = "other"


class MemoryFactRead(ApiModel):
    id: int
    text: str
    category: FactCategory
    source_conversation_id: str
    source_conversation_title: str
    updated_at: AwareDatetime


# --- The compactor's structured output (sent to Claude, not part of the HTTP API) ---------


class FactOperation(BaseModel):
    """One change to the user's facts, decided by the compactor."""

    action: Literal["add", "update", "delete"]
    fact_id: int | None = Field(
        description="The [id] of the existing fact to update or delete. Null for add."
    )
    text: str = Field(
        description="The fact as one short, self-contained sentence. For delete, the fact removed."
    )
    category: FactCategory


class FactOperations(BaseModel):
    operations: list[FactOperation]
