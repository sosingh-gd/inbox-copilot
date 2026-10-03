import logging


def configure_logging(level: str) -> None:
    """Single logging configuration point, called once at startup."""
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
