import logging
from contextvars import ContextVar

# A tag such as "[conv=3d9a1c2e msg=7f1c0b9d] " put on every log line while a chat message is
# handled, so the lines of one message (sub-agents included) can be picked out. Context
# variables are copied into new asyncio tasks and threads, so the tag follows the work.
_log_tag: ContextVar[str] = ContextVar("log_tag", default="")


def set_log_context(**fields: str) -> None:
    """Tag the following log lines in this context, e.g. `set_log_context(conv=..., msg=...)`.
    Ids are shortened to 8 characters, which is plenty to tell messages apart."""
    _log_tag.set("[" + " ".join(f"{k}={v[:8]}" for k, v in fields.items()) + "] ")


class _LogTagFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.log_tag = _log_tag.get()
        return True


def configure_logging(level: str) -> None:
    """Single logging configuration point, called once at startup.

    `level` applies to the app's own loggers. Libraries stay at INFO or above, so DEBUG shows
    the app's step-by-step detail without the HTTP client's connection chatter.
    """
    app_level = logging.getLevelNamesMapping()[level.upper()]
    logging.basicConfig(
        level=max(app_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(log_tag)s%(message)s",
    )
    logging.getLogger("app").setLevel(app_level)
    for handler in logging.getLogger().handlers:
        handler.addFilter(_LogTagFilter())
