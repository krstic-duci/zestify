# Rate Limits
LOGIN_RATE_LIMIT = "5/minute"
GENERAL_RATE_LIMIT = "10/minute"

# Cookie Settings
COOKIE_NAME = "auth_token"
COOKIE_MAX_AGE = 86400  # 24 hours

# Allowed HTML Tags for Sanitization
ALLOWED_TAGS = ["div", "h3", "ul", "li", "span", "button"]

# API Settings
# NOTE: if we change model we MUST also change the .env file GEMINI_API_KEY
LLM_MODEL = "gemini-2.5-flash"
