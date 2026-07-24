from .base import AgentConfig, AgentType
from ..registry import AgentRegistry
from ..capabilities.preview import GenerateCoverCapability

config = AgentConfig(
    id=AgentType.PREVIEW,
    name="Preview Agent",
    description="Генерирует статичное превью (обложку) для видео-контента.",
    dependencies=[AgentType.PROMPT_DIRECTOR, AgentType.RETAIL],
    outputs=[
        "variants",
        "aspect_ratio",
        "catalog_item_id"
    ],
    capabilities=[
        GenerateCoverCapability
    ]
)

AgentRegistry.register(config)
