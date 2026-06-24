import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import jwt
from app.config.settings import settings

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"

class JWTError(Exception):
    """Base JWT error."""
    pass

class TokenExpiredError(JWTError):
    """Raised when token has expired."""
    pass

class InvalidTokenError(JWTError):
    """Raised when token signature is invalid or decode fails."""
    pass

def encode_token(payload: Dict[str, Any], expires_in: int = 3600) -> str:
    """
    Encode payload into a JWT token signed with settings.JWT_SECRET.
    Adds 'exp' and 'iat' claims.
    """
    to_encode = payload.copy()
    now = datetime.now(timezone.utc)
    to_encode.update({
        "iat": now,
        "exp": now + timedelta(seconds=expires_in)
    })
    try:
        token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)
        return token
    except Exception as e:
        logger.exception("Failed to encode JWT token")
        raise JWTError(f"Encoding failed: {e}") from e

def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode JWT token using settings.JWT_SECRET.
    Validates expiration, signature, and format.
    Raises TokenExpiredError or InvalidTokenError on failure.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError as e:
        logger.warning("Token expired signature")
        raise TokenExpiredError("Token has expired.") from e
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token signature: {e}")
        raise InvalidTokenError("Invalid token signature or payload.") from e
    except Exception as e:
        logger.exception("Unexpected error decoding token")
        raise JWTError(f"Unexpected decoding error: {e}") from e

def verify_jwt_module() -> bool:
    """
    Self-verification function to test encode, decode, expiration, and invalid token handling.
    """
    try:
        test_payload = {"user_id": "test-uuid-123"}
        
        # 1. Test encoding and decoding
        token = encode_token(test_payload, expires_in=10)
        decoded = decode_token(token)
        if decoded.get("user_id") != test_payload["user_id"]:
            raise JWTError("Decoded payload does not match original payload")
            
        # 2. Test expiration handling
        expired_token = encode_token(test_payload, expires_in=-10) # already expired
        try:
            decode_token(expired_token)
            raise JWTError("Decoding expired token did not raise ExpiredSignatureError")
        except TokenExpiredError:
            pass # Expected
            
        # 3. Test invalid token signature
        try:
            invalid_token = token + "invalid_suffix"
            decode_token(invalid_token)
            raise JWTError("Decoding invalid token did not raise InvalidTokenError")
        except InvalidTokenError:
            pass # Expected
            
        print("✓ JWT working")
        return True
    except Exception as e:
        logger.error(f"JWT self-verification failed: {e}")
        return False
