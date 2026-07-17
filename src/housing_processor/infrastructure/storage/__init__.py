from pathlib import Path
from uuid import uuid4

from housing_processor.application.ports.storage import StoredFile


class LocalFileStorage:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._sources = root / "sources"
        self._exports = root / "exports"
        self._sources.mkdir(parents=True, exist_ok=True)
        self._exports.mkdir(parents=True, exist_ok=True)

    def save_source(self, content: bytes, filename: str) -> StoredFile:
        key = f"sources/{uuid4().hex}_{filename}"
        path = self._root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return StoredFile(storage_key=key, filename=filename, size_bytes=len(content))

    def save_export(self, content: bytes, filename: str) -> StoredFile:
        key = f"exports/{uuid4().hex}_{filename}"
        path = self._root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return StoredFile(storage_key=key, filename=filename, size_bytes=len(content))

    def open(self, storage_key: str):
        return (self._root / storage_key).open("rb")

    def resolve_path(self, storage_key: str) -> Path:
        return self._root / storage_key
