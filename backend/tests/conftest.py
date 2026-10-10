"""
Pytest configuration for LexRisk backend tests.
Sets up environment variables so tests can run without a real .env file.
"""
import os
import pytest

# Set test environment variables before any app module is imported
os.environ.setdefault("GEMINI_API_KEY", "test_gemini_key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("FAISS_INDEX_DIR", "/tmp/test_indexes")
