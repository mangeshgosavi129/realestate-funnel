"""
LLM API helpers with retry logic and robust error handling.
Provides production-grade reliability for LLM API calls.
"""
import json
import re
import time
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps

logger = logging.getLogger(__name__)


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON object from text that may contain thinking/reasoning before JSON.
    Handles cases where model outputs reasoning before the actual JSON.
    
    Args:
        text: Raw text that may contain JSON embedded in reasoning
        
    Returns:
        Parsed dict or None if extraction failed
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
    # Pattern: find the first { and match to its closing }
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


def llm_call_with_retry(
    api_call: Callable,
    fallback_parser: Optional[Callable] = None,
    max_retries: int = 2,
    retry_delay: float = 0.5,
    step_name: str = "LLM"
) -> Dict[str, Any]:
    """
    Execute LLM API call with retry logic and graceful fallback.
    
    Args:
        api_call: Function that makes the API call and returns response
        fallback_parser: Optional function to parse failed/partial responses
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        step_name: Name of the step for logging
        
    Returns:
        Parsed JSON response dict
        
    Raises:
        Exception: If all retries fail and no fallback is available
    """
    last_error = None
    last_failed_generation = None
    
    for attempt in range(max_retries):
        try:
            response = api_call()
            content = response.choices[0].message.content
            
            # Try direct JSON parse
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Try extraction from text
                extracted = extract_json_from_text(content)
                if extracted:
                    logger.info(f"{step_name}: Extracted JSON from text response")
                    return extracted
                raise
                
        except Exception as e:
            last_error = e
            error_str = str(e)
            
            # Extract failed_generation from error if available
            if "'failed_generation':" in error_str:
                try:
                    # Parse the error message to get failed_generation
                    import ast
                    error_dict = ast.literal_eval(error_str.split(" - ", 1)[1])
                    last_failed_generation = error_dict.get('error', {}).get('failed_generation', '')
                except:
                    pass
            
            if attempt < max_retries - 1:
                logger.warning(
                    f"{step_name}: Attempt {attempt + 1} failed, retrying in {retry_delay}s... "
                    f"Error: {type(e).__name__}"
                )
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"{step_name}: All {max_retries} attempts failed")
    
    # Try fallback parser on failed generation
    if fallback_parser and last_failed_generation:
        try:
            result = fallback_parser(last_failed_generation)
            if result:
                logger.info(f"{step_name}: Fallback parser recovered from failed generation")
                return result
        except Exception as e:
            logger.warning(f"{step_name}: Fallback parser also failed: {e}")
    
    # Try extracting from failed_generation text
    if last_failed_generation:
        extracted = extract_json_from_text(last_failed_generation)
        if extracted:
            logger.info(f"{step_name}: Extracted JSON from failed_generation")
            return extracted
    
    # Re-raise last error
    raise last_error
