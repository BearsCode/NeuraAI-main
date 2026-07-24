from .base import AgentConfig, AgentType
from ..registry import AgentRegistry
from ..capabilities.retail import BuildCatalogCapability

config = AgentConfig(
    id=AgentType.RETAIL,
    name="Retail Agent",
    description="Фоновый процесс извлечения каталога из файлов и фото/меню.",
    dependencies=[AgentType.BUSINESS],
    outputs=[
        "retail_catalog"
    ],
    capabilities=[BuildCatalogCapability]
)

AgentRegistry.register(config)
