import bleach
import logging

logger = logging.getLogger(__name__)

ALLOWED_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
    'p', 'span', 'div', 'ul', 'ol', 'li', 
    'a', 'blockquote', 'code', 'pre', 
    'table', 'tr', 'td', 'th', 'strong', 'em', 'img'
]

ALLOWED_ATTRIBUTES = {
    '*': ['class'],
    'a': ['href', 'title'],
    'img': ['src', 'alt']
}

ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']

def sanitize_artifact_content(content: str, artifact_type: str) -> str:
    """
    Sanitize HTML content using bleach to prevent XSS.
    Markdown artifacts are bypassed as per requirements.
    """
    if artifact_type == "markdown":
        return content
        
    try:
        sanitized = bleach.clean(
            content,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=True
        )
        return sanitized
    except Exception as e:
        logger.error(f"Sanitization failed: {e}")
        return ""
