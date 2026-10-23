import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _airlines() -> dict[str, str]:
    path = Path(__file__).resolve().parents[1] / "data" / "airlines.json"
    return json.loads(path.read_text(encoding="utf-8"))


def airline_name(code: str) -> str:
    code = code.strip().upper()
    name = _airlines().get(code)
    return f"{name} ({code})" if name and name != code else code
