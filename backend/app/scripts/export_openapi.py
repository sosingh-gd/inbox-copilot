"""Export the OpenAPI spec without running the server.

Usage: uv run python -m app.scripts.export_openapi ../contract/openapi.json
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

# Exporting the spec needs no real secrets, so CI and fresh clones work without a .env.
for name in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "TOKEN_ENCRYPTION_KEY"):
    os.environ.setdefault(name, "openapi-export")
os.environ.setdefault("ANTHROPIC_API_KEY", "openapi-export")

from pydantic import BaseModel  # noqa: E402
from pydantic.json_schema import models_json_schema  # noqa: E402

from app.features.chat.events import ChatEvent  # noqa: E402
from app.main import create_app  # noqa: E402

# Models the frontend needs typed that never appear in a JSON request/response body,
# e.g. SSE event unions.
EXTRA_MODELS: list[type[BaseModel]] = [ChatEvent]


def build_spec() -> dict[str, Any]:
    spec = create_app().openapi()
    if EXTRA_MODELS:
        _, schema = models_json_schema(
            [(m, "serialization") for m in EXTRA_MODELS],
            ref_template="#/components/schemas/{model}",
            by_alias=True,
        )
        schemas = spec.setdefault("components", {}).setdefault("schemas", {})
        schemas.update(schema.get("$defs", {}))
    return spec


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "../contract/openapi.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build_spec(), indent=2, sort_keys=True) + "\n")  # stable diffs
    print(f"wrote {out}")
