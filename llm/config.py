"""
LLM Configuration for HTL Pipeline.
Uses Groq for fast, cost-effective inference.
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMConfig:
    """Configuration for LLM provider."""
    api_key: str
    model: str
    base_url: str

# Ensureenv is loaded if accessed directly
from pathlib import Path
from dotenv import load_dotenv

current_file_path = Path(__file__).resolve()
root_dir = current_file_path.parent.parent
env_path = root_dir / ".env.dev"

if env_path.exists() and not os.getenv("GROQ_API_KEY"):
    load_dotenv(dotenv_path=env_path, override=True)
    timeout: int
    
    # Cost optimization
    


def get_llm_config() -> LLMConfig:
    """
    Get LLM configuration from environment.
    Optimized for Groq's fast inference.
    """
    return LLMConfig(
        api_key=os.getenv("GROQ_API_KEY"),
        model=os.getenv("LLM_MODEL"),
        base_url=os.getenv("LLM_BASE_URL")
    )


# Singleton config instance
_config: Optional[LLMConfig] = None


def get_config() -> LLMConfig:
    """Get cached config instance."""
    global _config
    if _config is None:
        _config = get_llm_config()
    return _config
