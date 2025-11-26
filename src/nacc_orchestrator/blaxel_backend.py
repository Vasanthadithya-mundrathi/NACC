"""Blaxel AI Model Gateway backend for NACC orchestrator.

Blaxel is a cloud platform built for AI agents that provides:
- Model Gateway: Unified API access to multiple LLM providers
- Support for OpenAI-compatible endpoints (GPT models)
- Support for Gemini endpoints
- Built-in telemetry and cost control
"""

from __future__ import annotations

import os
import json
import logging
from typing import Any, Literal
import requests

logger = logging.getLogger(__name__)


class BlaxelBackend:
    """LLM backend using Blaxel Model Gateway.
    
    Blaxel provides a unified gateway to multiple model providers with:
    - OpenAI-compatible API (gpt-4o-mini, gpt-4o, etc.)
    - Gemini API (gemini-2-0-flash-exp, gemini-1.5-pro, etc.)
    - Built-in monitoring and cost control
    """
    
    def __init__(
        self,
        *,
        api_key: str | None = None,
        workspace: str | None = None,
        model: str = "gpt-4o-mini",
        endpoint_type: Literal["openai", "gemini"] = "openai",
        base_url: str = "https://run.blaxel.ai",
        timeout: float = 30.0
    ):
        """
        Initialize Blaxel backend.
        
        Args:
            api_key: Blaxel API key (defaults to BLAXEL_API_KEY env var)
            workspace: Blaxel workspace name (defaults to BLAXEL_WORKSPACE env var)
            model: Model to use:
                - OpenAI-compatible: gpt-4o-mini, gpt-4o, gpt-4-turbo, etc.
                - Gemini: gemini-2-0-flash-exp, gemini-1.5-pro, gemini-1.5-flash
            endpoint_type: API format - "openai" or "gemini"
            base_url: Blaxel gateway base URL
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.environ.get("BLAXEL_API_KEY")
        self.workspace = workspace or os.environ.get("BLAXEL_WORKSPACE")
        
        if not self.api_key:
            raise ValueError("Blaxel API key not provided and BLAXEL_API_KEY not set")
        if not self.workspace:
            raise ValueError("Blaxel workspace not provided and BLAXEL_WORKSPACE not set")
        
        self.model = model
        self.endpoint_type = endpoint_type
        self.base_url = base_url
        self.timeout = timeout
        
        # Build endpoint URL based on model type
        if endpoint_type == "openai":
            # OpenAI-compatible: https://run.blaxel.ai/{workspace}/models/{model}/v1/chat/completions
            self.endpoint_url = f"{base_url}/{workspace}/models/{model}/v1/chat/completions"
        else:  # gemini
            # Gemini: https://run.blaxel.ai/{workspace}/models/gemini-2-0-flash-exp/v1beta/models/{model}:generateContent
            # The first part uses the workload name (gemini-2-0-flash-exp), second part uses actual model
            self.endpoint_url = f"{base_url}/{workspace}/models/gemini-2-0-flash-exp/v1beta/models/{model}:generateContent"
    
    def complete(self, prompt: str, *, context: dict[str, Any] | None = None) -> str:
        """
        Generate completion using Blaxel Model Gateway.
        
        Args:
            prompt: The prompt to complete
            context: Optional context dict to append to prompt
            
        Returns:
            The completion text
        """
        # Build headers - Both OpenAI and Gemini use Bearer prefix
        headers = {
            "Content-Type": "application/json",
            "X-Blaxel-Workspace": self.workspace,
            "X-Blaxel-Authorization": f"Bearer {self.api_key}"
        }
        
        # Build request based on endpoint type
        if self.endpoint_type == "openai":
            return self._complete_openai(prompt, context, headers)
        else:
            return self._complete_gemini(prompt, context, headers)
    
    def _complete_openai(
        self,
        prompt: str,
        context: dict[str, Any] | None,
        headers: dict[str, str]
    ) -> str:
        """Complete using OpenAI-compatible API."""
        # Build messages
        messages = [
            {
                "role": "system",
                "content": "You are an intelligent network orchestrator assistant. Respond with structured JSON when asked to identify tools."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Add context if provided
        if context:
            messages[0]["content"] += f"\n\nContext: {json.dumps(context)}"
        
        # Make request
        payload = {
            "model": self.model,  # Model goes in the body for OpenAI format
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 2048
        }
        
        try:
            response = requests.post(
                self.endpoint_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Blaxel API error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise RuntimeError(f"Blaxel API error: {e}") from e
    
    def _complete_gemini(
        self,
        prompt: str,
        context: dict[str, Any] | None,
        headers: dict[str, str]
    ) -> str:
        """Complete using Gemini API format."""
        # Build prompt with context
        full_prompt = prompt
        if context:
            full_prompt = f"{prompt}\n\nContext: {json.dumps(context)}"
        
        # Gemini API format
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": full_prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 2048
            }
        }
        
        try:
            response = requests.post(
                self.endpoint_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            # Extract text from Gemini response format
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Blaxel Gemini API error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise RuntimeError(f"Blaxel Gemini API error: {e}") from e


def test_blaxel_backend():
    """Test the Blaxel backend with different models."""
    
    # Test configuration
    api_key = "bl_aaab2v2ljj61gumirbwukm9deyva37sq"
    workspace = "vasanthfeb13"
    
    test_prompt = """Analyze this query and tell me which tool to use: "create file test.txt with content hello"

Respond ONLY with JSON in this format:
{
    "tool": "write_file",
    "parameters": {"filename": "test.txt", "content": "hello"},
    "reasoning": "brief explanation"
}"""
    
    # Test OpenAI-compatible endpoint
    print("=" * 80)
    print("Testing Blaxel with GPT-4o-mini (OpenAI-compatible)")
    print("=" * 80)
    
    try:
        backend_gpt = BlaxelBackend(
            api_key=api_key,
            workspace=workspace,
            model="gpt-4o-mini",
            endpoint_type="openai"
        )
        
        response = backend_gpt.complete(test_prompt)
        print("\nResponse:")
        print(response)
        print()
        
        # Try to parse as JSON
        import re
        json_match = re.search(r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            print("Parsed JSON:")
            print(json.dumps(data, indent=2))
        print()
    except Exception as e:
        print(f"❌ GPT-4o-mini test failed: {e}\n")
    
    # Test Gemini endpoint
    print("=" * 80)
    print("Testing Blaxel with Gemini-2.0-flash (Gemini API)")
    print("=" * 80)
    
    try:
        backend_gemini = BlaxelBackend(
            api_key=api_key,
            workspace=workspace,
            model="gemini-2.0-flash",  # Using gemini-2.0-flash as requested
            endpoint_type="gemini"
        )
        
        response = backend_gemini.complete(test_prompt)
        print("\nResponse:")
        print(response)
        print()
        
        # Try to parse as JSON
        import re
        json_match = re.search(r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            print("Parsed JSON:")
            print(json.dumps(data, indent=2))
        print()
    except Exception as e:
        print(f"❌ Gemini test failed: {e}\n")


if __name__ == "__main__":
    test_blaxel_backend()
