import json
import re
import logging
from typing import Dict, Any, Optional, List

from openai import OpenAI
from llm.config import llm_config

logger = logging.getLogger(__name__)
logging.getLogger("llm").disabled = True
logging.getLogger("llm.api_helpers").disabled = True

# Initialize single OpenAI client
client = OpenAI(
    api_key=llm_config.api_key,
    base_url=llm_config.base_url,
)

def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON object from text that may contain thinking/reasoning before JSON.
    """
    if not text:
        return None
    
    text = text.strip()
    
    # If it's already valid JSON, parse it directly
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON object in the text
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    # Try markdown code block extraction
    code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except json.JSONDecodeError:
            pass
    
    return None

def make_api_call(
    messages: List[Dict[str, str]],
    response_format: Optional[Dict[str, Any]] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    step_name: str = "LLM"
) -> Dict[str, Any]:
    """
    Execute LLM API call without retries.
    
    Returns:
        Parsed JSON response dict
    """
    llm_logger = logging.getLogger("llm")

    # Set to True to see full prompts in terminal
    DEBUG_PROMPTS = True

    try:
        # Print full request for debugging
        if DEBUG_PROMPTS:
            print(f"\n{'='*60}")
            print(f"[{step_name}] REQUEST")
            print(f"{'='*60}")
            for msg in messages:
                print(f"--- {msg['role'].upper()} ---")
                print(msg['content'])
            print(f"{'='*60}\n")

        kwargs = {
            "model": llm_config.model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format:
            kwargs["response_format"] = response_format
        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        response = client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content

        # Print full response for debugging
        if DEBUG_PROMPTS:
            print(f"\n{'='*60}")
            print(f"[{step_name}] RESPONSE")
            print(f"{'='*60}")
            print(content)
            print(f"{'='*60}\n")

        # Try direct JSON parse
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try extraction from text
            extracted = extract_json_from_text(content)
            if extracted:
                print(f"{step_name}: Extracted JSON from text response")
                logger.info(f"{step_name}: Extracted JSON from text response")
                return extracted
            raise ValueError(f"{step_name}: Could not parse JSON from response: {content[:100]}...")
            
    except Exception as e:
        print(f"[LLM ERROR] {step_name}: {e}")
        logger.error(f"{step_name} API call failed: {e}")
        raise

