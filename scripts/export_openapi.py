"""Write the OpenAPI 3 spec for all services to docs/openapi.json."""

import json
from pathlib import Path

from dppmadera.app import app

out = Path("docs/openapi.json")
out.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
print(f"wrote {out}")
