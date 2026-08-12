"""Filesystem adapters preserving content-addressed and append-only semantics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .canonical import canonical_bytes
from .canonical import digest_json
from .errors import GardenError


_SENSITIVE_KEY_PARTS = (
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
)


def _contains_sensitive_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if any(part in lowered for part in _SENSITIVE_KEY_PARTS):
                return True
            if _contains_sensitive_key(item):
                return True
    elif isinstance(value, list):
        return any(_contains_sensitive_key(item) for item in value)
    return False


class ContentAddressedStore:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def put(self, value: dict[str, Any]) -> tuple[str, Path]:
        digest = digest_json(value)
        path = self.root / "sha256" / f"{digest}.json"
        payload = canonical_bytes(value)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_bytes() != payload:
            raise GardenError(f"content digest collision: {digest}")
        if not path.exists():
            path.write_bytes(payload)
        return digest, path


class AppendOnlyLedger:
    """Minimal release-store adapter; no target credentials are accepted."""

    def __init__(self, path: Path) -> None:
        self.path = path.resolve()

    def records(self) -> tuple[dict[str, Any], ...]:
        if not self.path.exists():
            return ()
        return tuple(
            json.loads(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line
        )

    def append(self, record: dict[str, Any]) -> None:
        release_id = record.get("release_id")
        if not isinstance(release_id, str) or not release_id:
            raise GardenError("release record requires release_id")
        if _contains_sensitive_key(record):
            raise GardenError("release record must not contain secret material")
        if any(item.get("release_id") == release_id for item in self.records()):
            raise GardenError(f"duplicate release record: {release_id}")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("ab") as stream:
            stream.write(canonical_bytes(record))
