"""Identity constants. Standard library only.

The TUI imports this module, not ``engine.py``, so reading the provider's
display name never pulls in the provider's SDK.
"""

PROVIDER_NAME = "OpenAI"
PROVIDER_HOMEPAGE = "https://openai.com"
PLATFORM = "openai"
API_KEY_ENV_VAR = "OPENAI_API_KEY"
API_KEY_PATTERN = r".+"
