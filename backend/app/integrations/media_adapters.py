import httpx
from abc import ABC, abstractmethod
from backend.app.core.configs import settings
import logging

logger = logging.getLogger(__name__)

class BaseMediaAdapter(ABC):
    pass

class BaseImageAdapter(BaseMediaAdapter):
    @abstractmethod
    async def generate_image(self, prompt: str, size: str = "1024x1024") -> str:
        pass

class TalkingHeadVideoAdapter(BaseMediaAdapter):
    @abstractmethod
    async def generate_video(self, script: str, avatar_id: str, voice_id: str) -> str:
        pass

class TextToVideoAdapter(BaseMediaAdapter):
    @abstractmethod
    async def generate_scene(self, prompt: str, image_url: str | None = None) -> str:
        pass

class DalleImageAdapter(BaseImageAdapter):
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    async def generate_image(self, prompt: str, size: str = "1024x1024") -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "dall-e-3",
                    "prompt": prompt,
                    "n": 1,
                    "size": size
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["url"]

class HeyGenVideoAdapter(TalkingHeadVideoAdapter):
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    async def generate_video(self, script: str, avatar_id: str, voice_id: str) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.heygen.com/v2/video/generate",
                headers={
                    "x-api-key": self.api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "video_inputs": [
                        {
                            "character": {
                                "type": "avatar",
                                "avatar_id": avatar_id
                            },
                            "voice": {
                                "type": "text",
                                "input_text": script,
                                "voice_id": voice_id
                            }
                        }
                    ],
                    "dimension": {"width": 1080, "height": 1920}
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["data"]["video_id"] # In a real app we'd poll for status, returning ID for now

class MockImageAdapter(BaseImageAdapter):
    async def generate_image(self, prompt: str, size: str = "1024x1024") -> str:
        return f"https://mock-image.com/{size}?prompt={prompt.replace(' ', '+')}"

class MockVideoAdapter(TalkingHeadVideoAdapter):
    async def generate_video(self, script: str, avatar_id: str, voice_id: str) -> str:
        return "mock-video-id-12345"

class KlingVideoAdapter(TextToVideoAdapter):
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    async def generate_scene(self, prompt: str, image_url: str | None = None) -> str:
        return "https://example.com/mock-kling-scene.mp4"

class MockSceneAdapter(TextToVideoAdapter):
    async def generate_scene(self, prompt: str, image_url: str | None = None) -> str:
        return "https://example.com/mock-scene.mp4"

def build_image_adapter() -> BaseImageAdapter:
    if settings.ai.provider == "mock":
        return MockImageAdapter()
        
    if settings.ai.openai and settings.ai.openai.api_key:
        api_key = settings.ai.openai.api_key.get_secret_value()
        return DalleImageAdapter(api_key=api_key)
        
    return MockImageAdapter()

def build_video_adapter() -> TalkingHeadVideoAdapter:
    if settings.ai.heygen and settings.ai.heygen.api_key:
        api_key = settings.ai.heygen.api_key.get_secret_value()
        return HeyGenVideoAdapter(api_key=api_key)

    return MockVideoAdapter()

def build_scene_adapter() -> TextToVideoAdapter:
    if settings.ai.provider == "mock":
        return MockSceneAdapter()
    return MockSceneAdapter()
