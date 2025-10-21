"""
Validation utilities for Translation API Gateway
"""

def validate_translation_request(data):
    """Validate translation request data"""
    errors = []

    if not isinstance(data, dict):
        errors.append("Request body must be JSON object")
        return False, errors

    # Check required fields
    required_fields = ['text', 'source', 'target']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(data[field], str):
            errors.append(f"Field {field} must be a string")
        elif not data[field].strip():
            errors.append(f"Field {field} cannot be empty")

    # Validate text length
    if 'text' in data and len(data['text']) > 10000:
        errors.append("Text too long (max 10000 characters)")

    # Validate language codes
    if 'source' in data and len(data['source']) > 10:
        errors.append("Source language code too long")
    if 'target' in data and len(data['target']) > 10:
        errors.append("Target language code too long")

    return len(errors) == 0, errors

def validate_api_config(config):
    """Validate API configuration"""
    errors = []

    if not config.get('url'):
        errors.append("API URL is required")
    elif not config['url'].startswith(('http://', 'https://')):
        errors.append("API URL must be a valid HTTP/HTTPS URL")

    if not config.get('model'):
        errors.append("Model name is required")

    # Temperature validation
    temperature = config.get('temperature', 1.0)
    try:
        temp_float = float(temperature)
        if not 0.0 <= temp_float <= 2.0:
            errors.append("Temperature must be between 0.0 and 2.0")
    except (ValueError, TypeError):
        errors.append("Temperature must be a valid number")

    return len(errors) == 0, errors