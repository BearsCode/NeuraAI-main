from .base import AgentConfig, AgentType
from ..registry import AgentRegistry
from ..capabilities.motion_product import (
    DetectObjectCapability,
    SelectStyleCapability,
    PlanScenesCapability,
    GenerateMotionVideoCapability,
    AssembleVideoCapability
)
from ..capabilities.checker import ValidateVideoCapability

config = AgentConfig(
    id=AgentType.MOTION_PRODUCT,
    name="Motion-Товар Агент",
    description="Создаёт кинематографичные 3D-подобные анимации товара.",
    dependencies=[AgentType.BUSINESS, AgentType.RETAIL],
    outputs=[
        "video_url"
    ],
    capabilities=[
        DetectObjectCapability,
        SelectStyleCapability,
        PlanScenesCapability,
        GenerateMotionVideoCapability,
        AssembleVideoCapability,
        ValidateVideoCapability
    ]
)

AgentRegistry.register(config)
