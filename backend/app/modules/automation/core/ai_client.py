from typing import Any, Dict, List, Literal, Type
import openai
from pydantic import BaseModel

try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None

Provider = Literal["openai", "anthropic"]

class AIClient:
    def __init__(self, openai_api_key: str, anthropic_api_key: str = "") -> None:
        self.openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
        if AsyncAnthropic and anthropic_api_key:
            self.anthropic_client = AsyncAnthropic(api_key=anthropic_api_key)
        else:
            self.anthropic_client = None

    async def generate_text(
        self, 
        messages: List[Dict[str, str]], 
        provider: Provider = "openai",
        model: str = "gpt-4o",
        **kwargs: Any
    ) -> str:
        if provider == "openai":
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=messages, # type: ignore
                **kwargs
            )
            return response.choices[0].message.content or ""
        
        if provider == "anthropic":
            if not self.anthropic_client:
                raise RuntimeError("Anthropic client is not initialized")
            
            system_msgs = [m["content"] for m in messages if m["role"] == "system"]
            system_prompt = system_msgs[0] if system_msgs else ""
            user_msgs = [m for m in messages if m["role"] != "system"]
            
            anthropic_kwargs = {
                "model": model,
                "messages": user_msgs,
                "max_tokens": kwargs.get("max_tokens", 4096),
            }
            if system_prompt:
                anthropic_kwargs["system"] = system_prompt
                
            response = await self.anthropic_client.messages.create(**anthropic_kwargs) # type: ignore
            return response.content[0].text # type: ignore
            
        raise ValueError(f"Unknown provider: {provider}")

    async def generate_json(
        self, 
        messages: List[Dict[str, str]], 
        schema: Type[BaseModel], 
        provider: Provider = "openai",
        model: str = "gpt-4o",
        **kwargs: Any
    ) -> Any:
        if provider == "openai":
            response = await self.openai_client.beta.chat.completions.parse(
                model=model,
                messages=messages, # type: ignore
                response_format=schema,
                **kwargs
            )
            return response.choices[0].message.parsed
            
        raise NotImplementedError("JSON generation is currently supported only via OpenAI provider.")

    async def generate_image(self, prompt: str, **kwargs: Any) -> str:
        """
        Generates an image using DALL-E 3 and returns the URL.
        """
        response = await self.openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            **kwargs
        )
        if response.data and response.data[0].url:
            return response.data[0].url
        raise RuntimeError("Failed to generate image URL")

    # --- Anthropic Message Batches API ---
    
    async def create_anthropic_batch(self, batch_requests: List[Dict[str, Any]]) -> str:
        """
        Submits a batch of requests to Anthropic's Message Batches API.
        `batch_requests` should be a list of dictionaries, each with 'custom_id' and 'params'.
        Returns the batch ID.
        """
        if not self.anthropic_client:
            raise RuntimeError("Anthropic client is not initialized")
            
        response = await self.anthropic_client.messages.batches.create(
            requests=batch_requests
        )
        return response.id

    async def get_anthropic_batch_status(self, batch_id: str) -> str:
        """
        Checks the status of an Anthropic Message Batch.
        Returns the processing_status (e.g., 'in_progress', 'ended', 'canceling').
        """
        if not self.anthropic_client:
            raise RuntimeError("Anthropic client is not initialized")
            
        response = await self.anthropic_client.messages.batches.retrieve(batch_id)
        return response.processing_status

    async def get_anthropic_batch_results(self, batch_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the results of a completed Anthropic Message Batch.
        Returns a list of parsed JSON objects.
        """
        if not self.anthropic_client:
            raise RuntimeError("Anthropic client is not initialized")
            
        results = []
        async for result in self.anthropic_client.messages.batches.results(batch_id):
            # Convert the Pydantic model or Anthropic object to a dict to make it easier to work with
            if hasattr(result, "model_dump"):
                results.append(result.model_dump())
            else:
                results.append(dict(result))
                
        return results

