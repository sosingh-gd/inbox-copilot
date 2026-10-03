from pydantic import Field

from app.core.schemas import ApiModel


class GoogleLoginRequest(ApiModel):
    code: str = Field(min_length=1, description="One-time authorization code from Google")


class CurrentUserRead(ApiModel):
    email: str
    scopes: list[str]
