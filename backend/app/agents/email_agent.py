from datetime import date

from app.features.emails.sources import EmailSource
from app.features.emails.tools import email_tools

from .models import HAIKU, AgentDefinition
from .prompts import render_prompt


def build_email_agent(source: EmailSource, today: date) -> AgentDefinition:
    return AgentDefinition(
        name="email",
        description="Reads, classifies and summarizes the user's recent emails, including deadlines.",
        system_prompt=render_prompt("email", today=today.isoformat()),
        tools=email_tools(source),
        model=HAIKU,
    )
