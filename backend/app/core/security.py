import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientError
from fastapi import HTTPException, status
from pydantic import BaseModel
from app.core.config import settings

class SupabaseUser(BaseModel):
    id: str
    email: str
    role: str

# PyJWKClient fetches Supabase's public keys and caches them for an hour, so a
# transient network blip doesn't re-hit the JWKS endpoint on every request.
# Handles ES256 (asymmetric) tokens that newer Supabase projects generate.
_jwks_client = PyJWKClient(
    f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json",
    cache_keys=True,
    lifespan=3600,
)

def verify_token(token: str) -> SupabaseUser:
    """
    Decodes and verifies a Supabase JWT (ES256 or HS256).
    Fetches the matching public key from Supabase's JWKS endpoint by kid,
    verifies the signature, and returns the authenticated user.
    """
    try:
        try:
            signing_key = _jwks_client.get_signing_key_from_jwt(token)
        except PyJWKClientError as e:
            # JWKS endpoint unreachable (e.g. transient DNS/network blip).
            # Fail clean with 503 instead of a 500 traceback so the client can retry.
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service temporarily unreachable, please retry.",
            ) from e

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256", "HS256"],  # accept all Supabase variants
            audience="authenticated",
        )

        if payload.get("role") != "authenticated":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authenticated",
            )

        return SupabaseUser(
            id=payload["sub"],
            email=payload.get("email", ""),
            role=payload.get("role", ""),
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
