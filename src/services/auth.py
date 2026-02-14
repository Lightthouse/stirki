import logging
import random

logger = logging.getLogger(__name__)


def generate_verification_code() -> str:
    """Generate a 4-digit verification code."""
    code = f"{random.randint(0, 9999):04d}"
    # MVP: log code instead of sending SMS
    logger.info("Verification code generated: %s", code)
    return code
