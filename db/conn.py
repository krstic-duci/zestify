from supabase import Client, create_client

from utils.config import SETTINGS

supabase: Client = create_client(
    SETTINGS.supabase_url,
    SETTINGS.supabase_service_role_key,
)
