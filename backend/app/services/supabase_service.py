import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.utils.supabase_client import supabase_client, get_anonymous_user_id, supabase_lock

logger = logging.getLogger(__name__)

def synchronized(func):
    def wrapper(*args, **kwargs):
        with supabase_lock:
            return func(*args, **kwargs)
    return wrapper

class SupabaseService:
    """
    Service layer providing CRUD operations and Storage interactions with Supabase.
    All client interactions are synchronized to prevent concurrent HTTP/2 stream issues.
    """

    # --- DATASETS ---
    @staticmethod
    @synchronized
    def create_dataset(filename: str, rows: int, columns: int, file_type: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Insert a dataset record."""
        if not user_id:
            user_id = get_anonymous_user_id()
        
        data = {
            "user_id": user_id,
            "filename": filename,
            "rows": rows,
            "columns": columns,
            "file_type": file_type
        }
        try:
            res = supabase_client.table("datasets").insert(data).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.error(f"Failed to create dataset in Supabase: {e}")
            raise e
        return {}

    # --- SESSIONS ---
    @staticmethod
    @synchronized
    def create_session(session_id: str, dataset_id: str, status: str = "active") -> Dict[str, Any]:
        """Insert a session record."""
        data = {
            "id": session_id,
            "dataset_id": dataset_id,
            "status": status
        }
        try:
            res = supabase_client.table("sessions").insert(data).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.error(f"Failed to create session in Supabase: {e}")
            raise e
        return {}

    @staticmethod
    @synchronized
    def touch_session(session_id: str) -> None:
        """Update last_accessed timestamp for a session."""
        try:
            supabase_client.table("sessions").update({
                "last_accessed": datetime.now(timezone.utc).isoformat()
            }).eq("id", session_id).execute()
        except Exception as e:
            logger.warning(f"Failed to touch session {session_id} in Supabase: {e}")

    # --- OPERATIONS ---
    @staticmethod
    @synchronized
    def create_operation(session_id: str, step_number: int, operation_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Insert an operation history record."""
        # Ensure is_active status is initialized to True in parameters
        if "is_active" not in parameters:
            parameters["is_active"] = True

        data = {
            "session_id": session_id,
            "step_number": step_number,
            "operation_type": operation_type,
            "parameters": parameters
        }
        try:
            res = supabase_client.table("operations").insert(data).execute()
            # Touch session last accessed
            # (touch_session will acquire the lock again, which is re-entrant?
            # Wait! threading.Lock is NOT re-entrant!
            # If we call touch_session from create_operation, and both are @synchronized,
            # it will DEADLOCK because threading.Lock is not re-entrant!
            # Oh! That is a very important catch!
            # We should use threading.RLock() instead of threading.Lock()!)
            SupabaseService.touch_session(session_id)
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.error(f"Failed to create operation in Supabase: {e}")
            raise e
        return {}

    @staticmethod
    @synchronized
    def deactivate_last_operation(session_id: str) -> Optional[Dict[str, Any]]:
        """
        Mark the last active operation for a session as undone.
        Sets is_active = False and undone_at timestamp inside parameters.
        Returns the updated operation row.
        """
        try:
            # Fetch all operations for session
            res = supabase_client.table("operations").select("*").eq("session_id", session_id).order("step_number", desc=True).execute()
            if not res.data:
                return None
            
            # Find the first active operation
            for op in res.data:
                params = op.get("parameters", {}) or {}
                if params.get("is_active", True):
                    params["is_active"] = False
                    params["undone_at"] = datetime.now(timezone.utc).isoformat()
                    
                    update_res = supabase_client.table("operations").update({
                        "parameters": params
                    }).eq("id", op["id"]).execute()
                    
                    # Touch session (inside RLock)
                    SupabaseService.touch_session(session_id)
                    if update_res.data:
                        return update_res.data[0]
                    break
        except Exception as e:
            logger.error(f"Failed to deactivate last operation for session {session_id}: {e}")
            raise e
        return None

    @staticmethod
    @synchronized
    def get_active_operations(session_id: str) -> List[Dict[str, Any]]:
        """Retrieve all active operations for a session in order."""
        try:
            res = supabase_client.table("operations").select("*").eq("session_id", session_id).order("step_number", desc=False).execute()
            if res.data:
                return [op for op in res.data if (op.get("parameters") or {}).get("is_active", True)]
        except Exception as e:
            logger.error(f"Failed to fetch operations for session {session_id}: {e}")
        return []

    # --- REPORTS ---
    @staticmethod
    @synchronized
    def create_report(session_id: str, report_url: str) -> Dict[str, Any]:
        """Insert a report record (saving storage path in report_url)."""
        data = {
            "session_id": session_id,
            "report_url": report_url
        }
        try:
            res = supabase_client.table("reports").insert(data).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.error(f"Failed to record report in Supabase: {e}")
            raise e
        return {}

    # --- EXPORTS ---
    @staticmethod
    @synchronized
    def create_export(session_id: str, format: str, file_url: str) -> Dict[str, Any]:
        """Insert an export record (saving storage path in file_url)."""
        data = {
            "session_id": session_id,
            "format": format,
            "file_url": file_url
        }
        try:
            res = supabase_client.table("exports").insert(data).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.error(f"Failed to record export in Supabase: {e}")
            raise e
        return {}

    # --- STORAGE ---
    @staticmethod
    @synchronized
    def upload_file(bucket_name: str, storage_path: str, file_content: bytes) -> str:
        """
        Upload raw file bytes to a Supabase storage bucket.
        Returns the relative storage path (e.g., '{user_id}/{filename}').
        """
        try:
            # Check if bucket is present or handle on conflict
            supabase_client.storage.from_(bucket_name).upload(
                path=storage_path,
                file=file_content,
                file_options={"cache-control": "3600", "upsert": "true"}
            )
            return storage_path
        except Exception as e:
            logger.error(f"Failed to upload file to bucket {bucket_name} at path {storage_path}: {e}")
            raise e

    @staticmethod
    @synchronized
    def download_file(bucket_name: str, storage_path: str) -> bytes:
        """Download raw file bytes from Supabase storage."""
        try:
            return supabase_client.storage.from_(bucket_name).download(storage_path)
        except Exception as e:
            logger.error(f"Failed to download file from bucket {bucket_name} at path {storage_path}: {e}")
            raise e

    @staticmethod
    @synchronized
    def generate_signed_url(bucket_name: str, storage_path: str, expires_in: int = 3600) -> str:
        """Generate a short-lived signed URL for a file in storage."""
        try:
            res = supabase_client.storage.from_(bucket_name).create_signed_url(storage_path, expires_in)
            if isinstance(res, dict):
                return res.get("signedURL") or res.get("signedUrl") or ""
            elif hasattr(res, "signed_url"):
                return res.signed_url
            elif hasattr(res, "get"):
                return res.get("signedURL") or res.get("signedUrl") or ""
            return str(res)
        except Exception as e:
            logger.error(f"Failed to generate signed URL for bucket {bucket_name} at path {storage_path}: {e}")
            raise e

    # --- ML ARCHITECT ---
    @staticmethod
    @synchronized
    def create_recommendation_feedback(
        session_id: str,
        recommended_algorithm: str,
        accepted: bool,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Record user feedback (accepted/rejected) on a recommended algorithm."""
        data = {
            "session_id": session_id,
            "recommended_algorithm": recommended_algorithm,
            "accepted": accepted,
        }
        if user_id:
            data["user_id"] = user_id
            
        try:
            res = supabase_client.table("recommendation_feedback").insert(data).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.error(f"Failed to record recommendation feedback in Supabase: {e}")
            raise e
        return {}

    @staticmethod
    @synchronized
    def create_ml_recommendation(
        session_id: str,
        goal: Optional[str],
        top_algorithm: str,
        confidence: float,
        recommendations: List[Dict[str, Any]],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Record the recommendation results in database."""
        data = {
            "session_id": session_id,
            "goal": goal,
            "top_algorithm": top_algorithm,
            "confidence": confidence,
            "recommendations": recommendations,
        }
        if user_id:
            data["user_id"] = user_id
            
        try:
            res = supabase_client.table("ml_recommendations").insert(data).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.error(f"Failed to record ML recommendation in Supabase: {e}")
            raise e
        return {}
