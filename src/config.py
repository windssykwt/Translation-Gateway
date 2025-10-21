"""
Configuration module for Translation API Gateway
Loads all settings from environment variables
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for all application settings"""

    # Main configuration
    SAFE_SEPARATOR = os.getenv("SAFE_SEPARATOR", "//////")
    ENABLE_CONTROL_LOG = os.getenv("ENABLE_CONTROL_LOG", "False").lower() == "true"
    ACTIVE_MODE = os.getenv("ACTIVE_MODE", "Cloud")

    # Server configuration
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", "5000"))
    SERVER_DEBUG = os.getenv("SERVER_DEBUG", "False").lower() == "true"

    @staticmethod
    def get_primary_cloud_config():
        """Get primary cloud API configuration"""
        return {
            "url": os.getenv("PRIMARY_CLOUD_URL", "https://api.intelligence.io.solutions/api/v1/chat/completions"),
            "key": os.getenv("PRIMARY_CLOUD_KEY", ""),
            "model": os.getenv("PRIMARY_CLOUD_MODEL", "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"),
            "temperature": float(os.getenv("PRIMARY_CLOUD_TEMPERATURE", "0.7")),
            "enable_context": os.getenv("PRIMARY_CLOUD_ENABLE_CONTEXT", "True").lower() == "true"
        }

    @staticmethod
    def get_secondary_cloud_config():
        """Get secondary cloud API configuration"""
        return {
            "url": os.getenv("SECONDARY_CLOUD_URL", "https://api.intelligence.io.solutions/api/v1/chat/completions"),
            "key": os.getenv("SECONDARY_CLOUD_KEY", ""),
            "model": os.getenv("SECONDARY_CLOUD_MODEL", "Qwen/Qwen3-Next-80B-A3B-Instruct"),
            "temperature": float(os.getenv("SECONDARY_CLOUD_TEMPERATURE", "0.7")),
            "enable_context": os.getenv("SECONDARY_CLOUD_ENABLE_CONTEXT", "True").lower() == "true"
        }

    @staticmethod
    def get_local_config():
        """Get local API configuration"""
        return {
            "url": os.getenv("LOCAL_API_URL", "http://localhost:11434/v1/chat/completions"),
            "key": os.getenv("LOCAL_API_KEY", ""),
            "model": os.getenv("LOCAL_API_MODEL", "zongwei/gemma3-translator:4b"),
            "temperature": float(os.getenv("LOCAL_API_TEMPERATURE", "0.0")),
            "enable_context": os.getenv("LOCAL_API_ENABLE_CONTEXT", "False").lower() == "true"
        }