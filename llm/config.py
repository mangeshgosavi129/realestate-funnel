"""
LLM Configuration for HTL Pipeline.
Uses Groq for fast, cost-effective inference.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMConfig:
    """Configuration for LLM provider."""
    api_key: str
    model: str
    base_url: str

# Load environment variables
current_file_path = Path(__file__).resolve()
root_dir = current_file_path.parent.parent
env_path = root_dir / ".env.dev"

if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)

# Exported configuration object
llm_config = LLMConfig(
    api_key=os.getenv("GROQ_API_KEY"),
    model=os.getenv("LLM_MODEL"),
    base_url=os.getenv("LLM_BASE_URL")
)
