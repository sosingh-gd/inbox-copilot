from typing import Annotated

from fastapi import Depends

from app.features.auth.deps import GoogleCredentialsDep

from .service import EmailService
from .sources import EmailSource, GmailEmailSource


def get_email_source(credentials: GoogleCredentialsDep) -> EmailSource:
    return GmailEmailSource(credentials)


def get_email_service(
    source: Annotated[EmailSource, Depends(get_email_source)],
) -> EmailService:
    return EmailService(source)


EmailServiceDep = Annotated[EmailService, Depends(get_email_service)]
