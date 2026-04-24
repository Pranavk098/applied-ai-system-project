import json
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path("game_log.jsonl")


def log_turn(entry: dict) -> None:
    """Append a structured entry to game_log.jsonl."""
    entry["timestamp"] = datetime.now(timezone.utc).isoformat()
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
