"""
Formatting utilities for Translation API Gateway
"""

import re
import html

class MORTFormatter:
    """Formatter for MORT translation format"""

    def __init__(self, separator="//////"):
        self.separator = separator

    def validate_and_fix_format(self, text):
        """Validate and fix MORT format"""
        if not text:
            return ""

        # Normalize line endings
        text = text.replace('\n', '\r\n').replace('\r\r\n', '\r\n')

        # Clean text
        cleaned_text = text.strip()

        # Remove separator at beginning
        cleaned_text = re.sub(r'^\s*' + re.escape(self.separator) + r'\s*\r\n', '', cleaned_text)

        # Remove separator at end
        cleaned_text = re.sub(r'\r\n\s*' + re.escape(self.separator) + r'\s*$', '', cleaned_text)

        # Split by separator and filter empty segments
        segments = [s.strip() for s in cleaned_text.split(self.separator) if s.strip()]

        # Return empty if no segments
        if not segments:
            return ""

        # Join segments with proper formatting
        return f"{self.separator}\r\n" + f"\r\n{self.separator}\r\n".join(segments) + f"\r\n"

    def extract_segments(self, text):
        """Extract individual segments from MORT format"""
        if not text:
            return []

        # Split by separator and filter empty segments
        segments = [s.strip() for s in text.split(self.separator) if s.strip()]
        return segments

    def clean_response(self, text):
        """Clean API response by removing unwanted characters and HTML entities"""
        if not text:
            return ""

        # Unescape HTML entities
        cleaned_text = html.unescape(text)

        # Remove extra whitespace
        cleaned_text = ' '.join(cleaned_text.split())

        return cleaned_text.strip()

def format_translation_response(translated_text, separator="//////"):
    """Format translation response in MORT format"""
    formatter = MORTFormatter(separator)
    return formatter.validate_and_fix_format(translated_text)

def sanitize_text(text):
    """Sanitize text by removing potentially harmful content"""
    if not text:
        return ""

    # Remove potential script injections
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Unescape HTML entities
    text = html.unescape(text)

    return text.strip()