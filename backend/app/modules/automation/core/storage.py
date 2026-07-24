import aiofiles
from pathlib import Path

class StorageManager:
    def __init__(self, base_path: str = "/tmp/neura_storage") -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save_file(self, filename: str, content: bytes) -> str:
        file_path = self.base_path / filename
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        return str(file_path)

    async def read_file(self, filename: str) -> bytes:
        file_path = self.base_path / filename
        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()
