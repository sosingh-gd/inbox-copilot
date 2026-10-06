from app.features.auth.deps import GoogleCredentialsDep

from .sources import EmailSource, GmailEmailSource


def get_email_source(credentials: GoogleCredentialsDep) -> EmailSource:
    return GmailEmailSource(credentials)
