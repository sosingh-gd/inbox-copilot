import json
from collections.abc import AsyncIterator, Sequence
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.features.chat.deps import get_chat_model
from app.features.chat.llm import Completion, LlmError, LlmEvent, LlmMessage, TextChunk
from app.features.chat.schemas import ModelChoice, ReasoningLevel
from tests.conftest import create_user, sign_in


class FakeChatModel:
    def __init__(self) -> None:
        self.reply = ["Hello", " there"]
        self.refuse = False
        self.error: LlmError | None = None
        self.calls: list[dict[str, Any]] = []

    async def stream(
        self,
        *,
        system: str,
        messages: Sequence[LlmMessage],
        model: ModelChoice,
        reasoning: ReasoningLevel,
    ) -> AsyncIterator[LlmEvent]:
        self.calls.append({"system": system, "messages": list(messages), "model": model})
        if self.error:
            raise self.error
        for text in self.reply:
            yield TextChunk(text)
        yield Completion(refused=self.refuse, input_tokens=10, output_tokens=2)


@pytest.fixture
def llm(app: FastAPI) -> FakeChatModel:
    fake = FakeChatModel()
    app.dependency_overrides[get_chat_model] = lambda: fake
    return fake


def sse_events(body: str) -> list[dict[str, Any]]:
    return [
        json.loads(line.removeprefix("data: "))
        for line in body.splitlines()
        if line.startswith("data: ")
    ]


def send(client: TestClient, content: str, **extra: Any) -> list[dict[str, Any]]:
    response = client.post("/api/v1/chat/runs/stream", json={"content": content, **extra})
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/event-stream")
    return sse_events(response.text)


def test_new_conversation_streams_and_persists_the_reply(
    signed_in_client: TestClient, llm: FakeChatModel
) -> None:
    events = send(signed_in_client, "Draft a follow-up", agent="inbox", model="haiku")

    assert [e["type"] for e in events] == [
        "run_started",
        "text_delta",
        "text_delta",
        "run_completed",
    ]
    assert events[-1]["usage"] == {"inputTokens": 10, "outputTokens": 2}
    conversation_id = events[0]["conversationId"]

    detail = signed_in_client.get(f"/api/v1/chat/conversations/{conversation_id}").json()
    assert detail["title"] == "Draft a follow-up"
    assert detail["model"] == "haiku"
    assert [(m["role"], m["content"]) for m in detail["messages"]] == [
        ("user", "Draft a follow-up"),
        ("assistant", "Hello there"),
    ]
    assert llm.calls[0]["model"] == ModelChoice.haiku


def test_follow_up_sends_history_and_keeps_the_agent(
    signed_in_client: TestClient, llm: FakeChatModel
) -> None:
    first = send(signed_in_client, "Hi", agent="calendar")
    conversation_id = first[0]["conversationId"]

    send(signed_in_client, "And tomorrow?", conversationId=conversation_id, agent="general")

    assert [m.content for m in llm.calls[1]["messages"]] == ["Hi", "Hello there", "And tomorrow?"]
    listing = signed_in_client.get("/api/v1/chat/conversations").json()
    assert len(listing) == 1
    assert listing[0]["agent"] == "calendar"


def test_refusal_fails_the_run_without_saving_a_reply(
    signed_in_client: TestClient, llm: FakeChatModel
) -> None:
    llm.refuse = True

    events = send(signed_in_client, "Something")

    assert events[-1] == {
        "type": "run_failed",
        "code": "refused",
        "message": "Claude declined to answer this request.",
    }
    detail = signed_in_client.get(
        f"/api/v1/chat/conversations/{events[0]['conversationId']}"
    ).json()
    assert [m["role"] for m in detail["messages"]] == ["user"]


def test_failed_turn_is_merged_into_the_next_user_turn(
    signed_in_client: TestClient, llm: FakeChatModel
) -> None:
    llm.error = LlmError("rate_limited", "busy")
    events = send(signed_in_client, "First")
    assert events[-1]["code"] == "rate_limited"

    llm.error = None
    send(signed_in_client, "Second", conversationId=events[0]["conversationId"])

    assert [(m.role, m.content) for m in llm.calls[1]["messages"]] == [("user", "First\n\nSecond")]


def test_other_users_conversations_are_not_found(
    client: TestClient, db: Session, llm: FakeChatModel
) -> None:
    owner = create_user(db)
    sign_in(client, db, owner, session_id="owner")
    conversation_id = send(client, "Private")[0]["conversationId"]

    intruder = create_user(db, google_sub="google-456", email="intruder@example.com")
    sign_in(client, db, intruder, session_id="intruder")

    assert client.get(f"/api/v1/chat/conversations/{conversation_id}").status_code == 404
    response = client.post(
        "/api/v1/chat/runs/stream", json={"content": "hi", "conversationId": conversation_id}
    )
    assert response.status_code == 404
    assert client.get("/api/v1/chat/conversations").json() == []


def test_chat_requires_sign_in(client: TestClient, llm: FakeChatModel) -> None:
    response = client.post("/api/v1/chat/runs/stream", json={"content": "hi"})

    assert response.status_code == 401
    assert llm.calls == []


def test_rejects_unknown_model(signed_in_client: TestClient, llm: FakeChatModel) -> None:
    response = signed_in_client.post(
        "/api/v1/chat/runs/stream", json={"content": "hi", "model": "gpt"}
    )

    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "model"
