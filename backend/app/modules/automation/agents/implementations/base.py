from enum import Enum
from typing import List, Type
from pydantic import BaseModel
from ..capabilities.base import Capability

class AgentType(str, Enum):
    BUSINESS = "business"
    MARKETING = "marketing"
    BRAND = "brand"
    TRAINING = "training"
    PLANNER = "planner"
    CONTENT = "content"
    IMAGE = "image"
    VIDEO = "video"
    CHECKER = "checker"
    PUBLISHER = "publisher"
    ANALYTICS = "analytics"
    RETAIL = "retail"
    CEO = "ceo"
    UGC_AVATAR = "ugc_avatar"
    MOTION_PRODUCT = "motion_product"
    TIMELAPSE = "timelapse"
    PREVIEW = "preview"
    EDITOR = "editor"
    PROMPT_DIRECTOR = "prompt_director"

class AgentConfig(BaseModel):
    id: AgentType
    name: str
    description: str
    dependencies: List[AgentType]
    outputs: List[str]
    capabilities: List[Type[Capability]]
