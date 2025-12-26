import json
import os
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Tuple

from .config import DEFAULT_STORAGE_FILENAME

APP_DIR_NAME = "PoE Stash Regex Generator"


@dataclass
class SavedRegexEntry:
    label: str
    entries: list[str]
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)


def _serialize_entry(entry: SavedRegexEntry) -> dict[str, Any]:
    return asdict(entry)


def _deserialize_entry(data: dict[str, Any]) -> SavedRegexEntry:
    return SavedRegexEntry(
        label=str(data.get("label", "")),
        entries=[str(value) for value in data.get("entries", [])],
        created_at=str(data.get("created_at", "")),
        metadata=dict(data.get("metadata", {})),
    )


def _default_base_dir() -> Path:
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata)
    return Path.home() / "AppData" / "Roaming"


def default_storage_path(base_dir: str | None = None) -> str:
    root = Path(base_dir) if base_dir else _default_base_dir()
    return str(root / APP_DIR_NAME / DEFAULT_STORAGE_FILENAME)


def save_entries(path: str, entries: Iterable[SavedRegexEntry]) -> None:
    storage_path = Path(path)
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [_serialize_entry(entry) for entry in entries]

    tmp_path = storage_path.with_suffix(storage_path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="ascii")
    tmp_path.replace(storage_path)


def load_entries(path: str) -> Tuple[list[SavedRegexEntry], list[str]]:
    storage_path = Path(path)
    if not storage_path.exists():
        return [], []

    try:
        raw = storage_path.read_text(encoding="ascii")
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        return [], [f"Failed to load saved regex data: {exc}"]

    if not isinstance(payload, list):
        return [], ["Saved regex data is not a list."]

    entries: list[SavedRegexEntry] = []
    for item in payload:
        if isinstance(item, dict):
            entries.append(_deserialize_entry(item))

    return entries, []


def new_entry(label: str, entries: list[str], metadata: dict[str, Any] | None = None) -> SavedRegexEntry:
    return SavedRegexEntry(
        label=label,
        entries=entries,
        created_at=datetime.now(timezone.utc).isoformat(),
        metadata=metadata or {},
    )
