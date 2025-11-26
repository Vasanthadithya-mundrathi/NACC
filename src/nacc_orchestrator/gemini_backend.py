"""Gemini backend for NACC orchestrator using official Google Generative AI SDK."""

from __future__ import annotations

import os
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class GeminiBackend:
    """LLM backend using Google's Generative AI (Gemini).

    Uses the official google-generativeai package with API key authentication.
    """

    def __init__(self, api_key: str | None = None, model: str = "gemini-1.5-flash"):
        if not GENAI_AVAILABLE:
            raise ImportError("google-generativeai not installed. Install with: pip install google-generativeai")
        
        # Use provided key, env var, or fallback to test key
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or "AIzaSyC9iEQeOZ9a69rTWcj7i-s6s8dU0bcqmpY"
        if not self.api_key:
            raise ValueError("Gemini API key not provided and GEMINI_API_KEY not set")
        
        # Configure the API
        genai.configure(api_key=self.api_key)
        self.model = model
        
        # Create the model instance
        self.client = genai.GenerativeModel(model)

    def complete(self, prompt: str, *, context: dict[str, Any] | None = None) -> str:
        # Build the full prompt with context if provided
        full_prompt = prompt
        if context:
            full_prompt = f"Context: {json.dumps(context)}\n\n{prompt}"

        try:
            # Generate content
            response = self.client.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=1024,
                )
            )
            
            # Extract text from response
            return response.text.strip() if response.text else ""

        except Exception as e:
            logger.exception("Gemini API error: %s", e)
            raise RuntimeError(f"Gemini API error: {e}") from e


def _test_gemini():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("GEMINI_API_KEY not set; skipping test")
        return
    b = GeminiBackend(api_key=key)
    print(b.complete('Respond with JSON: {"tool":"test","parameters":{}}'))


if __name__ == "__main__":
    _test_gemini()
