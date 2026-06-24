import logging
import threading
from supabase import create_client, Client
from app.config.settings import settings

logger = logging.getLogger(__name__)

# Thread lock for Supabase client calls (re-entrant RLock to support nested calls)
supabase_lock = threading.RLock()

# Initialize Supabase client
try:
    supabase_client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
except Exception as e:
    logger.exception("Failed to initialize Supabase client")
    raise e

def get_anonymous_user_id() -> str:
    """
    Dynamically retrieve the first available user ID from profiles table
    to serve as a fallback/anonymous user ID during development,
    preventing foreign key constraint failures.
    """
    with supabase_lock:
        try:
            res = supabase_client.table("profiles").select("id").limit(1).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]["id"]
        except Exception as e:
            logger.warning(f"Could not retrieve anonymous user ID from profiles: {e}")
        # Fallback to the known test user ID created during verification/initialization
        return "612f98e4-fbf0-4de2-8d8a-a884dc7d1fce"
