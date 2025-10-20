"""
Ollama provider for Medallion
"""

from typing import Dict, Any, Optional, List
import requests
import json


class OllamaProvider:
    """Ollama provider for local LLM inference"""
    
    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 30):
        """Initialize Ollama provider
        
        Args:
            base_url: Ollama server base URL
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
    
    def generate(self, prompt: str, model: str = "llama3.1", 
                system_prompt: Optional[str] = None,
                temperature: float = 0.7,
                max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Generate text using Ollama
        
        Args:
            prompt: Input prompt
            model: Model name to use
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary with generated text and metadata
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            return {
                "text": result.get("response", ""),
                "tokens_used": result.get("eval_count", 0),
                "finish_reason": "stop",
                "metadata": {
                    "model": result.get("model"),
                    "total_duration": result.get("total_duration"),
                    "eval_duration": result.get("eval_duration"),
                }
            }
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama request failed: {e}")
    
    def list_models(self) -> List[str]:
        """List available models
        
        Returns:
            List of available model names
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            return [model["name"] for model in result.get("models", [])]
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to list Ollama models: {e}")
    
    def pull_model(self, model: str) -> Dict[str, Any]:
        """Pull a model from Ollama registry
        
        Args:
            model: Model name to pull
            
        Returns:
            Pull result information
        """
        payload = {"name": model}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/pull",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            return {"status": "success", "model": model}
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to pull Ollama model {model}: {e}")
