from itsdangerous import URLSafeTimedSerializer

from utils.config import SETTINGS

serializer = URLSafeTimedSerializer(SETTINGS.auth_token_key)
