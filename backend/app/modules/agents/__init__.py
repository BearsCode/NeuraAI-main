from backend.app.modules.agents.base import AgentRegistry, BaseAgent
from backend.app.modules.agents.business_agent import BusinessAgent
from backend.app.modules.agents.marketing_agent import MarketingAgent
from backend.app.modules.agents.brand_agent import BrandAgent
from backend.app.modules.agents.content_agent import ContentAgent
from backend.app.modules.agents.image_agent import ImageAgent
from backend.app.modules.agents.video_agent import VideoAgent
from backend.app.modules.agents.retail_agent import RetailAgent
from backend.app.modules.agents.ceo_agent import CEOAgent
from backend.app.modules.agents.checker_agent import CheckerAgent
from backend.app.modules.agents.training_agent import TrainingAgent

from backend.app.modules.agents.editor_agent import EditorAgent
from backend.app.modules.agents.timelapse_agent import TimelapseAgent
from backend.app.modules.agents.avatar_agent import AvatarAgent
from backend.app.modules.agents.motion_agent import MotionAgent

agent_registry = AgentRegistry()
agent_registry.register("business", BusinessAgent())
agent_registry.register("marketing", MarketingAgent())
agent_registry.register("brand", BrandAgent())
agent_registry.register("content", ContentAgent())
agent_registry.register("image", ImageAgent())
agent_registry.register("video", VideoAgent())
agent_registry.register("retail", RetailAgent())
agent_registry.register("ceo", CEOAgent())
agent_registry.register("checker", CheckerAgent())
agent_registry.register("training", TrainingAgent())
agent_registry.register("editor", EditorAgent())
agent_registry.register("timelapse", TimelapseAgent())
agent_registry.register("avatar", AvatarAgent())
agent_registry.register("motion", MotionAgent())

__all__ = [
    "agent_registry",
    "AgentRegistry",
    "BaseAgent",
    "BusinessAgent",
    "MarketingAgent",
    "BrandAgent",
    "ContentAgent",
    "ImageAgent",
    "VideoAgent",
    "RetailAgent",
    "CEOAgent",
    "CheckerAgent",
    "TrainingAgent",
    "EditorAgent",
    "TimelapseAgent",
    "AvatarAgent",
    "MotionAgent",
]
