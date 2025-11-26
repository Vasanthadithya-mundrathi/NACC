"""
NACC Backend Manager - Unified Backend Configuration and Switching
Supports all 7 AI backends with runtime switching capability
"""

import os
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BackendType(str, Enum):
    """All available AI backends"""
    MODAL = "modal"
    GEMINI = "gemini"
    OPENAI = "openai"
    CEREBRAS = "cerebras"
    BLAXEL_OPENAI = "blaxel-openai"
    BLAXEL_GEMINI = "blaxel-gemini"
    DOCKER_MISTRAL = "docker-mistral"
    LOCAL_HEURISTIC = "local-heuristic"


@dataclass
class BackendConfig:
    """Configuration for a specific backend"""
    name: str
    backend_type: BackendType
    display_name: str
    description: str
    requires_api_key: bool
    is_free: bool
    api_key_env_var: Optional[str] = None
    api_key_url: Optional[str] = None
    timeout: float = 90.0
    model: Optional[str] = None
    container_id: Optional[str] = None
    environment: Optional[Dict[str, Any]] = None


# All available backends with their configurations
AVAILABLE_BACKENDS = {
    BackendType.MODAL: BackendConfig(
        name="modal",
        backend_type=BackendType.MODAL,
        display_name="Modal A100 + IBM Granite MoE",
        description="FREE serverless GPU (A100 80GB) with IBM Granite-3.0-3B-A800M (MoE). ~60s response time.",
        requires_api_key=False,
        is_free=True,
        timeout=120.0,
        model="ibm-granite/granite-3.0-3b-a800m-instruct",
        environment={
            "modal_app_id": "ap-8PaCvfA0O7brdDuCMSuNRV",
            "gpu": "A100",
            "note": "Deployed on Modal, always warm"
        }
    ),
    
    BackendType.GEMINI: BackendConfig(
        name="gemini",
        backend_type=BackendType.GEMINI,
        display_name="Google Gemini",
        description="Google's Gemini 2.0 Flash (fast and accurate). Requires your API key.",
        requires_api_key=True,
        is_free=False,
        api_key_env_var="GEMINI_API_KEY",
        api_key_url="https://aistudio.google.com/",
        timeout=90.0,
        model="gemini-2.0-flash-exp"
    ),
    
    BackendType.OPENAI: BackendConfig(
        name="openai",
        backend_type=BackendType.OPENAI,
        display_name="OpenAI GPT-4",
        description="OpenAI GPT-4o-mini or GPT-4o. Requires your API key.",
        requires_api_key=True,
        is_free=False,
        api_key_env_var="OPENAI_API_KEY",
        api_key_url="https://platform.openai.com/",
        timeout=90.0,
        model="gpt-4o-mini"
    ),
    
    BackendType.CEREBRAS: BackendConfig(
        name="cerebras",
        backend_type=BackendType.CEREBRAS,
        display_name="Cerebras Fast Inference",
        description="Ultra-fast inference with Llama models. Requires your API key.",
        requires_api_key=True,
        is_free=False,
        api_key_env_var="CEREBRAS_API_KEY",
        api_key_url="https://cloud.cerebras.ai/",
        timeout=60.0,
        model="llama-3.3-70b"
    ),
    
    BackendType.BLAXEL_OPENAI: BackendConfig(
        name="blaxel-openai",
        backend_type=BackendType.BLAXEL_OPENAI,
        display_name="Blaxel OpenAI (10 FREE)",
        description="FREE 10 requests via Blaxel gateway to OpenAI GPT-4o-mini. No API key needed!",
        requires_api_key=False,
        is_free=True,
        timeout=90.0,
        model="gpt-4o-mini",
        environment={
            "note": "10 free requests via Blaxel",
            "blaxel_managed": True
        }
    ),
    
    BackendType.BLAXEL_GEMINI: BackendConfig(
        name="blaxel-gemini",
        backend_type=BackendType.BLAXEL_GEMINI,
        display_name="Blaxel Gemini (10 FREE)",
        description="FREE 10 requests via Blaxel gateway to Google Gemini. No API key needed!",
        requires_api_key=False,
        is_free=True,
        timeout=90.0,
        model="gemini-2-0-flash-exp",
        environment={
            "note": "10 free requests via Blaxel",
            "blaxel_managed": True
        }
    ),
    
    BackendType.DOCKER_MISTRAL: BackendConfig(
        name="docker-mistral",
        backend_type=BackendType.DOCKER_MISTRAL,
        display_name="Docker Mistral (Local)",
        description="Local Mistral-NeMo 12B via Docker. No API key, fully offline.",
        requires_api_key=False,
        is_free=True,
        timeout=90.0,
        model="mistral-nemo:latest",
        container_id="mistral-7b-instruct",
        environment={
            "local": True,
            "offline": True
        }
    ),
    
    BackendType.LOCAL_HEURISTIC: BackendConfig(
        name="local-heuristic",
        backend_type=BackendType.LOCAL_HEURISTIC,
        display_name="Local Heuristic (Fallback)",
        description="Simple rule-based fallback. No AI, no API key needed.",
        requires_api_key=False,
        is_free=True,
        timeout=5.0,
        environment={
            "note": "Rule-based fallback, no AI model"
        }
    ),
}


class BackendManager:
    """Manages backend switching and configuration"""
    
    def __init__(self):
        self.current_backend: Optional[BackendType] = None
        self.current_config: Optional[BackendConfig] = None
    
    def get_available_backends(self) -> Dict[str, BackendConfig]:
        """Get all available backends"""
        return AVAILABLE_BACKENDS
    
    def get_free_backends(self) -> Dict[str, BackendConfig]:
        """Get only free backends (no API key required)"""
        return {
            k: v for k, v in AVAILABLE_BACKENDS.items() 
            if v.is_free
        }
    
    def get_backend_config(self, backend_type: BackendType) -> BackendConfig:
        """Get configuration for a specific backend"""
        return AVAILABLE_BACKENDS.get(backend_type)
    
    def validate_backend(self, backend_type: BackendType, api_key: Optional[str] = None) -> tuple[bool, str]:
        """Validate if a backend can be used"""
        config = self.get_backend_config(backend_type)
        
        if not config:
            return False, f"Backend {backend_type} not found"
        
        # Check if API key is required
        if config.requires_api_key:
            # Check environment variable
            env_key = os.getenv(config.api_key_env_var) if config.api_key_env_var else None
            
            if not api_key and not env_key:
                return False, f"API key required. Get one from: {config.api_key_url}"
        
        return True, "Backend is valid"
    
    def switch_backend(self, backend_type: BackendType, api_key: Optional[str] = None) -> tuple[bool, str]:
        """Switch to a different backend"""
        valid, message = self.validate_backend(backend_type, api_key)
        
        if not valid:
            return False, message
        
        self.current_backend = backend_type
        self.current_config = self.get_backend_config(backend_type)
        
        logger.info(f"Switched to backend: {self.current_config.display_name}")
        return True, f"Successfully switched to {self.current_config.display_name}"
    
    def get_current_backend(self) -> Optional[BackendConfig]:
        """Get current active backend configuration"""
        return self.current_config
    
    def generate_orchestrator_config(self, backend_type: BackendType, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Generate orchestrator.yml compatible configuration"""
        config = self.get_backend_config(backend_type)
        
        result = {
            "kind": config.name,
            "timeout": config.timeout,
        }
        
        # Add API key if provided or from environment
        if config.requires_api_key:
            key = api_key or os.getenv(config.api_key_env_var)
            if key:
                result["container_id"] = key
        elif config.container_id:
            result["container_id"] = config.container_id
        
        # Add environment
        if config.environment or config.model:
            result["environment"] = config.environment or {}
            if config.model:
                result["environment"]["model"] = config.model
        
        return result
    
    def get_backend_status(self) -> Dict[str, Any]:
        """Get status of all backends"""
        status = {}
        
        for backend_type, config in AVAILABLE_BACKENDS.items():
            valid, message = self.validate_backend(backend_type)
            status[config.name] = {
                "display_name": config.display_name,
                "is_available": valid,
                "status_message": message,
                "is_free": config.is_free,
                "requires_api_key": config.requires_api_key,
                "is_active": backend_type == self.current_backend
            }
        
        return status


# Global instance
backend_manager = BackendManager()


def get_backend_manager() -> BackendManager:
    """Get the global backend manager instance"""
    return backend_manager
