from typing import Any, Protocol, runtime_checkable

@runtime_checkable
class Capability(Protocol):
    async def execute(self, **kwargs: Any) -> Any: ...
