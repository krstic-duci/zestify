from itsdangerous import URLSafeTimedSerializer
from utils.config import settings

serializer = URLSafeTimedSerializer(settings.auth_token_key)
