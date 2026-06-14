from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from jose.backends import RSAKey
import httpx
import base64
import os
from dotenv import load_dotenv

load_dotenv()

security = HTTPBearer()
ALGORITHM = os.getenv("ALGORITHM", "RS256")
AUTH_JWKS_URL = os.getenv("AUTH_JWKS_URL", "http://localhost:8081/v1/auth/.well-known/jwks.json")

_cached_public_key = None

def get_public_key():
    global _cached_public_key
    if _cached_public_key:
        return _cached_public_key

    try:
        response = httpx.get(AUTH_JWKS_URL, timeout=5)
        response.raise_for_status()
        jwks = response.json()
        key_data = jwks["keys"][0]

        # Rekonstruuj klucz RSA z JWKS
        def b64_to_int(s: str) -> int:
            padded = s + "=" * (4 - len(s) % 4)
            return int.from_bytes(base64.urlsafe_b64decode(padded), "big")

        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
        from cryptography.hazmat.backends import default_backend

        pub_numbers = RSAPublicNumbers(
            e=b64_to_int(key_data["e"]),
            n=b64_to_int(key_data["n"]),
        )
        public_key = pub_numbers.public_key(default_backend())

        from cryptography.hazmat.primitives import serialization
        _cached_public_key = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return _cached_public_key

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Nie można pobrać klucza z auth-service: {e}")


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    token = credentials.credentials
    try:
        public_key = get_public_key()
        payload = jwt.decode(token, public_key, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Nieprawidłowy token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Nieprawidłowy lub wygasły token")