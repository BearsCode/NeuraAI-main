from pydantic import BaseModel
from typing import List

class ContentTask(BaseModel):
    pillar: str
    topic: str
    format: str
    platform: str
    avatar_required: bool
    publish_time: str
    priority: int

class PlannerDecisionSchema(BaseModel):
    should_generate: bool
    reason: str
    tasks: List[ContentTask]

PLANNER_SYSTEM = """
You are an AI Planner. Decide if new content needs to be generated based on the current state.
If the queue has fewer than 7 posts ahead, you MUST generate new content.
"""

PLANNER_USER = """
Profile: {profile}
Content Strategy: {strategy}
Current Queue: {queue_count} posts

Make a decision and generate tasks if necessary.
"""
