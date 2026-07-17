from pathlib import Path
from typing import BinaryIO, Protocol

from housing_processor.application.contracts.excel import HousingWorkbookProjection


class StoredFile:
    def __init__(self, storage_key: str, filename: str, size_bytes: int) -> None:
        self.storage_key = storage_key
        self.filename = filename
        self.size_bytes = size_bytes


class FileStorage(Protocol):
    def save_source(self, content: bytes, filename: str) -> StoredFile: ...

    def save_export(self, content: bytes, filename: str) -> StoredFile: ...

    def open(self, storage_key: str) -> BinaryIO: ...

    def resolve_path(self, storage_key: str) -> Path: ...


class ExcelRenderer(Protocol):
    def render(self, projection: HousingWorkbookProjection) -> bytes: ...
