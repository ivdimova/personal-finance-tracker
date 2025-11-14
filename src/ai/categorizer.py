"""AI-powered transaction categorization using Ollama."""

import os
import logging
from typing import Dict, Optional
from src.ai.client import get_ollama_client
from src.ai.prompts import CATEGORIZATION_PROMPT

logger = logging.getLogger(__name__)


def categorize_transaction(
    description: str,
    amount: float,
    merchant: str = "Unknown"
) -> Optional[Dict[str, any]]:
    """
    Use AI to categorize a financial transaction.

    Args:
        description: Transaction description
        amount: Transaction amount
        merchant: Merchant name

    Returns:
        Dict with 'category' and 'confidence', or None if failed
        Example: {'category': 'Food & Dining', 'confidence': 0.95}
    """
    # Check if AI is enabled
    ai_enabled = os.getenv("AI_ENABLED", "true").lower() == "true"
    if not ai_enabled:
        logger.debug("AI categorization disabled")
        return None

    try:
        # Get Ollama client
        client = get_ollama_client()

        # Check if service is available
        if not client.is_available():
            logger.warning("Ollama service not available")
            return None

        # Format the prompt
        prompt = CATEGORIZATION_PROMPT.format(
            description=description,
            merchant=merchant,
            amount=abs(amount)
        )

        # Generate response
        result = client.generate_json(prompt)

        if not result:
            logger.warning("Failed to get AI categorization response")
            return None

        # Validate response structure
        if 'category' not in result:
            logger.error(f"Invalid AI response format: {result}")
            return None

        category = result.get('category', '').strip()
        confidence = float(result.get('confidence', 0.0))

        # Validate confidence is between 0 and 1
        if not (0.0 <= confidence <= 1.0):
            logger.warning(f"Invalid confidence value: {confidence}")
            confidence = 0.5

        logger.info(
            f"AI categorized transaction '{description}' as '{category}' "
            f"(confidence: {confidence:.2f})"
        )

        return {
            'category': category,
            'confidence': confidence
        }

    except Exception as e:
        logger.error(f"Error in AI categorization: {e}", exc_info=True)
        return None


def should_use_ai_category(
    ai_result: Optional[Dict[str, any]],
    min_confidence: float = 0.75
) -> bool:
    """
    Determine if AI categorization result should be used.

    Args:
        ai_result: Result from categorize_transaction()
        min_confidence: Minimum confidence threshold

    Returns:
        True if AI result should be used
    """
    if not ai_result:
        return False

    confidence = ai_result.get('confidence', 0.0)
    return confidence >= min_confidence
