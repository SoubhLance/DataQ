import pytest
import time
from app.utils.jwt import (
    encode_token,
    decode_token,
    TokenExpiredError,
    InvalidTokenError
)

def test_jwt_encode_decode():
    payload = {"user_id": "test-uuid-999", "role": "admin"}
    token = encode_token(payload, expires_in=10)
    assert isinstance(token, str)
    
    decoded = decode_token(token)
    assert decoded["user_id"] == "test-uuid-999"
    assert decoded["role"] == "admin"
    assert "exp" in decoded
    assert "iat" in decoded

def test_jwt_expired():
    payload = {"user_id": "expired-user"}
    # Token expires immediately (-5 seconds)
    token = encode_token(payload, expires_in=-5)
    
    with pytest.raises(TokenExpiredError):
        decode_token(token)

def test_jwt_invalid_signature():
    payload = {"user_id": "invalid-signature-user"}
    token = encode_token(payload, expires_in=10)
    
    # Tamper with the token
    invalid_token = token + "abc"
    with pytest.raises(InvalidTokenError):
        decode_token(invalid_token)

def test_jwt_empty_token():
    with pytest.raises(InvalidTokenError):
        decode_token("")
