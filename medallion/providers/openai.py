"""
OpenAI provider for Medallion
"""

from typing import Dict, Any, Optional, List
import requests
import json
import os


class OpenAIProvider:
    """OpenAI provider for hosted LLM inference"""
    
    def __init__(self, api_key: Optional[str] = None, 
                 base_url: str = "https://api.openai.com/v1",
                 timeout: int = 30):
        """Initialize OpenAI provider
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            base_url: OpenAI API base URL
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
    
    def generate(self, prompt: str, model: str = "gpt-3.5-turbo",
                system_prompt: Optional[str] = None,
                temperature: float = 0.7,
                max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Generate text using OpenAI
        
        Args:
            prompt: Input prompt
            model: Model name to use
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary with generated text and metadata
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            choice = result["choices"][0]
            usage = result["usage"]
            
            return {
                "text": choice["message"]["content"],
                "tokens_used": usage["total_tokens"],
                "finish_reason": choice["finish_reason"],
                "metadata": {
                    "model": result["model"],
                    "prompt_tokens": usage["prompt_tokens"],
                    "completion_tokens": usage["completion_tokens"],
                }
            }
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"OpenAI request failed: {e}")
    
    def get_embeddings(self, text: str, model: str = "text-embedding-ada-002") -> List[float]:
        """Get embeddings for text
        
        Args:
            text: Text to embed
            model: Embedding model to use
            
        Returns:
            List of embedding values
        """
        payload = {
            "model": model,
            "input": text
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/embeddings",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result["data"][0]["embedding"]
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"OpenAI embeddings request failed: {e}")
    
    def list_models(self) -> List[str]:
        """List available models
        
        Returns:
            List of available model names
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return [model["id"] for model in result["data"]]
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to list OpenAI models: {e}")
