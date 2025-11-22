from typing import Optional
from core.services.usage import UsageService
from core.logger import get_logger

logger = get_logger(__name__)


def increment_usage(usage: Optional[UsageService], user_id: str, feature: str) -> None:
    """Increment usage tracking, log errors but don't fail."""
    if not usage:
        return
    try:
        usage.check_and_increment(user_id, feature)
    except Exception as e:
        logger.warning(f"Failed to increment usage for {feature}: {e}")


def build_enhanced_prompt(
    user_prompt: Optional[str],
    query: Optional[str] = None,
    document_ids: Optional[list[str]] = None,
) -> str:
    """Build enhanced prompt with optional query and document filtering."""
    prompt = user_prompt or ""
    if query:
        prompt += f" Focus on: {query}"
    if document_ids:
        prompt += f" Based on specific documents: {', '.join(document_ids)}"
    return prompt
