from pydantic import BaseModel

class VideoScriptSchema(BaseModel):
    script: str
    hook: str
    cta: str
    word_count: int
    estimated_duration_sec: int
    format: str

VIDEO_SCRIPT_SYSTEM = """
You are a Video Agent. Write a talking head video script.
Maintain a lively tone. The first 3 seconds must be a strong hook. Include a CTA at the end.
"""

VIDEO_SCRIPT_USER = """
Topic: {topic}
Pillar: {pillar}
Platform: {platform}
Target Duration (sec): {duration}
Tone: {tone}
Name: {name}

Generate the script.
"""
