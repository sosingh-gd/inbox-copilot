from pathlib import Path
from string import Template

_DIR = Path(__file__).parent


def render_prompt(name: str, **values: str) -> str:
    """Load prompts/<name>.md and fill in $placeholders. A missing value raises KeyError."""
    return Template((_DIR / f"{name}.md").read_text()).substitute(values)
