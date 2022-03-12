from dataclasses import asdict
import json
from typing import Any, Dict

from battle.arena import Arena


class JSONEncoder(json.JSONEncoder):
    """Minimizes JSON string length by reducing resolution of floats, convert bool to int, and transpose"""

    def encode(self, a) -> str:
        if isinstance(a, bool):
            return super().encode(1 if a else 0)
        if isinstance(a, float):
            return f"{round(a,1):g}"
        if isinstance(a, dict):
            items = (f'"{k}"{self.key_separator}{self.encode(v)}' for k, v in a.items())
            return f"{{{self.item_separator.join(items)}}}"
        if isinstance(a, (list, tuple)):
            if len(a) and isinstance(a[0], dict):
                transposed: Dict[str, Any] = {k: [e[k] for e in a] for k in a[0].keys()}
                transposed["_t"] = True
                return self.encode(transposed)
            return f"[{self.item_separator.join(self.encode(x) for x in a)}]"
        return super().encode(a)


def state_as_json(arena: Arena):
    d = asdict(arena)
    return json.dumps(d, separators=(",", ":"), cls=JSONEncoder)
