import logging
from typing import Mapping, Tuple
from whatsapp_receive.config import config

logger = logging.getLogger(__name__)

def verify_webhook(params: Mapping[str, str]) -> Tuple[str | Mapping, int]:
    """
    Verify webhook subscription from Meta.
    This is the GET request Meta sends to verify the webhook URL.
    """
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    logger.info("Verification began")
    
    if not (mode and token):
        return {"status": "error", "message": "Missing parameters"}, 400
    
    # Check if token matches the configured verify token
    if mode == "subscribe" and challenge:
        if token == config.VERIFY_TOKEN:
            logger.info("Webhook verification successful")
            return str(challenge), 200
        else:
            logger.warning(f"Verify token mismatch")
    
    return {"status": "error", "message": "Verification failed"}, 403
