"""
API Provider Configuration for NACC
Supports Docker (local testing), Anthropic Claude, OpenAI GPT-4, and Modal
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
import os


class AIProvider(Enum):
    """Available AI providers"""
    DOCKER = "docker"  # Local Docker Desktop AI (Mistral-NeMo) - FREE for testing
    ANTHROPIC = "anthropic"  # Claude 3.5 Sonnet - $3/MTok input, $15/MTok output
    OPENAI = "openai"  # GPT-4 Turbo - $10/MTok input, $30/MTok output
    MODAL = "modal"  # Modal hosted models - Variable pricing
    CEREBRAS = "cerebras"  # Cerebras API - Free tier available


@dataclass
class AIConfig:
    """AI provider configuration"""
    provider: AIProvider
    model_name: str
    timeout: float
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    
    # Cost tracking (per 1M tokens)
    cost_per_million_input: float = 0.0
    cost_per_million_output: float = 0.0
    
    @classmethod
    def docker_local(cls, timeout: float = 30.0) -> 'AIConfig':
        """
        Docker Desktop AI (Mistral-NeMo 12B)
        FREE - Perfect for local testing and development
        """
        return cls(
            provider=AIProvider.DOCKER,
            model_name="mistral-nemo",
            timeout=timeout,
            cost_per_million_input=0.0,
            cost_per_million_output=0.0
        )
    
    @classmethod
    def anthropic_claude(cls, timeout: float = 30.0) -> 'AIConfig':
        """
        Anthropic Claude 3.5 Sonnet
        Cost: $3/MTok input, $15/MTok output
        Best for: Complex reasoning, multi-step planning, code generation
        """
        return cls(
            provider=AIProvider.ANTHROPIC,
            model_name="claude-3-5-sonnet-20241022",
            timeout=timeout,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            base_url="https://api.anthropic.com/v1",
            max_tokens=8192,
            temperature=0.7,
            cost_per_million_input=3.0,
            cost_per_million_output=15.0
        )
    
    @classmethod
    def openai_gpt4(cls, timeout: float = 30.0) -> 'AIConfig':
        """
        OpenAI GPT-4 Turbo
        Cost: $10/MTok input, $30/MTok output
        Best for: General purpose, fast responses
        """
        return cls(
            provider=AIProvider.OPENAI,
            model_name="gpt-4-turbo-preview",
            timeout=timeout,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://api.openai.com/v1",
            max_tokens=4096,
            temperature=0.7,
            cost_per_million_input=10.0,
            cost_per_million_output=30.0
        )
    
    @classmethod
    def modal_hosted(cls, model: str = "mistralai/Mistral-7B-Instruct-v0.3", timeout: float = 30.0) -> 'AIConfig':
        """
        Modal hosted models
        Cost: Variable based on compute time
        Best for: Batch processing, custom models
        """
        return cls(
            provider=AIProvider.MODAL,
            model_name=model,
            timeout=timeout,
            api_key=os.getenv("MODAL_TOKEN"),
            base_url=os.getenv("MODAL_ENDPOINT"),
            max_tokens=4096,
            temperature=0.7,
            cost_per_million_input=2.0,  # Estimate
            cost_per_million_output=10.0  # Estimate
        )
    
    @classmethod
    def cerebras_free(cls, timeout: float = 30.0) -> 'AIConfig':
        """
        Cerebras API (Free Tier)
        Cost: FREE for reasonable usage
        Best for: Testing, prototyping
        """
        return cls(
            provider=AIProvider.CEREBRAS,
            model_name="llama3.1-8b",
            timeout=timeout,
            api_key=os.getenv("CEREBRAS_API_KEY"),
            base_url="https://api.cerebras.ai/v1",
            max_tokens=4096,
            temperature=0.7,
            cost_per_million_input=0.0,
            cost_per_million_output=0.0
        )
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a request"""
        input_cost = (input_tokens / 1_000_000) * self.cost_per_million_input
        output_cost = (output_tokens / 1_000_000) * self.cost_per_million_output
        return input_cost + output_cost
    
    def __str__(self) -> str:
        cost_str = "FREE" if self.cost_per_million_input == 0 else f"${self.cost_per_million_input}/MTok in, ${self.cost_per_million_output}/MTok out"
        return f"{self.provider.value}:{self.model_name} (timeout={self.timeout}s, cost={cost_str})"


class AIProviderFactory:
    """Factory for creating AI providers"""
    
    @staticmethod
    def create(config: AIConfig) -> 'AIProvider':
        """Create appropriate AI provider based on config"""
        if config.provider == AIProvider.DOCKER:
            from src.nacc_ui.ai_intent_parser import AIIntentParser
            return AIIntentParser(
                model_name=config.model_name,
                timeout=config.timeout,
                use_ai=True,
                use_fallback=False
            )
        elif config.provider == AIProvider.ANTHROPIC:
            # Will implement when switching to production
            raise NotImplementedError("Anthropic integration coming soon")
        elif config.provider == AIProvider.OPENAI:
            # Will implement when switching to production
            raise NotImplementedError("OpenAI integration coming soon")
        elif config.provider == AIProvider.MODAL:
            # Will implement when switching to production
            raise NotImplementedError("Modal integration coming soon")
        elif config.provider == AIProvider.CEREBRAS:
            # Will implement when switching to production
            raise NotImplementedError("Cerebras integration coming soon")
        else:
            raise ValueError(f"Unknown provider: {config.provider}")


# Default configuration for local testing
DEFAULT_CONFIG = AIConfig.docker_local(timeout=30.0)

# Production configurations (will be used after testing)
PRODUCTION_CONFIGS = {
    "anthropic": AIConfig.anthropic_claude(),
    "openai": AIConfig.openai_gpt4(),
    "modal": AIConfig.modal_hosted(),
    "cerebras": AIConfig.cerebras_free()
}


def print_cost_comparison():
    """Print cost comparison of all providers"""
    print("\n" + "="*80)
    print("AI PROVIDER COST COMPARISON (per 1 million tokens)")
    print("="*80)
    
    configs = [
        ("Docker Local (Testing)", AIConfig.docker_local()),
        ("Anthropic Claude 3.5", AIConfig.anthropic_claude()),
        ("OpenAI GPT-4 Turbo", AIConfig.openai_gpt4()),
        ("Modal Hosted", AIConfig.modal_hosted()),
        ("Cerebras Free Tier", AIConfig.cerebras_free())
    ]
    
    for name, config in configs:
        cost_str = "FREE" if config.cost_per_million_input == 0 else f"${config.cost_per_million_input:.2f} input, ${config.cost_per_million_output:.2f} output"
        print(f"  {name:30} {cost_str}")
    
    print("\nESTIMATED COSTS PER 1000 REQUESTS (avg 500 input + 200 output tokens):")
    print("-" * 80)
    
    input_tokens = 500 * 1000
    output_tokens = 200 * 1000
    
    for name, config in configs:
        cost = config.estimate_cost(input_tokens, output_tokens)
        cost_str = "FREE" if cost == 0 else f"${cost:.2f}"
        print(f"  {name:30} {cost_str}")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    print_cost_comparison()
    
    print("RECOMMENDED STRATEGY:")
    print("  1. ✅ Development/Testing: Docker Local (FREE)")
    print("  2. 🚀 Production: Anthropic Claude ($3-15/MTok) for best reasoning")
    print("  3. 💰 Budget Option: Cerebras (FREE) or Modal ($2-10/MTok)")
    print("  4. 💸 Emergency: OpenAI GPT-4 ($10-30/MTok)\n")
