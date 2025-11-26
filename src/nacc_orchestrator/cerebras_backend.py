"""Cerebras AI backend for NACC orchestrator."""

from __future__ import annotations

import os
from typing import Any
import json
import logging

logger = logging.getLogger(__name__)

try:
    from cerebras.cloud.sdk import Cerebras
    CEREBRAS_AVAILABLE = True
except ImportError:
    CEREBRAS_AVAILABLE = False


class CerebrasBackend:
    """LLM backend using Cerebras AI API."""
    
    def __init__(self, api_key: str | None = None, model: str = "zai-glm-4.6"):
        """
        Initialize Cerebras backend.
        
        Args:
            api_key: Cerebras API key (defaults to CEREBRAS_API_KEY env var)
            model: Model to use (default: zai-glm-4.6, also available: llama3.1-8b, llama3.1-70b)
        """
        if not CEREBRAS_AVAILABLE:
            raise ImportError(
                "cerebras-cloud-sdk not installed. "
                "Install with: pip install cerebras-cloud-sdk"
            )
        
        self.api_key = api_key or os.environ.get("CEREBRAS_API_KEY")
        if not self.api_key:
            raise ValueError("Cerebras API key not provided and CEREBRAS_API_KEY not set")
        
        self.model = model
        self.client = Cerebras(api_key=self.api_key)
    
    def complete(self, prompt: str, *, context: dict[str, Any] | None = None) -> str:
        """
        Generate completion using Cerebras AI.
        
        Args:
            prompt: The prompt to complete
            context: Optional context dict to append to prompt
            
        Returns:
            The completion text
        """
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
        
        try:
            # Use non-streaming for simpler integration
            response = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                stream=False,
                max_completion_tokens=2048,
                temperature=0.3,  # Lower temperature for more deterministic responses
                top_p=0.95
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise RuntimeError(f"Cerebras API error: {e}") from e


def test_cerebras_backend():
    """Test the Cerebras backend."""
    api_key = "csk-xv4r86nnncyxheje3ry5j9pe6k36wf2nvh3t5v4c9h4v34kc"
    
    backend = CerebrasBackend(api_key=api_key)
    
    # Test prompt
    test_prompt = """Analyze this query and tell me which tool to use: "create file test.txt with content hello"

Respond ONLY with JSON in this format:
{
    "tool": "write_file",
    "parameters": {"filename": "test.txt", "content": "hello"},
    "reasoning": "brief explanation"
}"""
    
    response = backend.complete(test_prompt)
    print("Cerebras Response:")
    print(response)
    print()
    
    # Try to parse as JSON
    try:
        import re
        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            print("Parsed JSON:")
            print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Could not parse as JSON: {e}")


if __name__ == "__main__":
    test_cerebras_backend()
