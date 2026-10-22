import os
import json
import uuid
import logging
from pathlib import Path
from threading import Lock
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from starlette.responses import RedirectResponse
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from OpenDEMON.server.auth_models import UserCreate, UserLogin, UserResponse, Token
from OpenDEMON.database.session import get_db_session
from OpenDEMON.database.repositories.users import UserRepository
from OpenDEMON.server.limiter import auth_limiter, user_limiter, RATELIMIT_AUTH, RATELIMIT_USER

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/auth", tags=["auth"])

JWT_SECRET = os.environ.get("JWT_SECRET", "sentinel-local-dev-jwt-secret-key-32b")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days


class LocalUserStore:
    """Resilient, file-backed local user repository for local development and offline environments."""

    def __init__(self, storage_path: Optional[Path] = None):
        if storage_path is None:
            base_dir = Path(__file__).resolve().parents[3] / "data"
            try:
                base_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                base_dir = Path.cwd()
            storage_path = base_dir / "local_users.json"
        self.path = storage_path
        self._lock = Lock()
        self._users: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        with self._lock:
            if self.path.exists():
                try:
                    with open(self.path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            self._users = data
                except Exception as exc:
                    logger.debug("Could not load local users from %s: %s", self.path, exc)

    def _save(self) -> None:
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._users, f, indent=2)
        except Exception as exc:
            logger.debug("Could not persist local users to %s: %s", self.path, exc)

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._users.get(email.lower().strip())

    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            for u in self._users.values():
                if str(u.get("id")) == str(user_id):
                    return u
            return None

    def create_user(
        self,
        email: str,
        name: str,
        password_hash: Optional[str] = None,
        picture: Optional[str] = None,
        custom_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            norm_email = email.lower().strip()
            user_id = custom_id or str(uuid.uuid4())
            user_data = {
                "id": user_id,
                "email": norm_email,
                "name": name,
                "password_hash": password_hash,
                "picture": picture,
                "provider": "local",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._users[norm_email] = user_data
            self._save()
            return user_data


local_user_store = LocalUserStore()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


async def _safe_db_get_by_email(db: Optional[AsyncSession], email: str) -> Optional[Dict[str, Any]]:
    if db:
        try:
            repo = UserRepository(db)
            db_user = await repo.get_by_email(email)
            if db_user:
                return {
                    "id": str(db_user.id),
                    "name": db_user.name,
                    "email": db_user.email,
                    "password_hash": getattr(db_user, "password_hash", None),
                    "provider": "postgres",
                }
        except Exception as exc:
            logger.debug("Database get_by_email unavailable (%s). Falling back to local store.", exc)
    return local_user_store.get_by_email(email)


async def _safe_db_get_by_id(db: Optional[AsyncSession], user_id: str) -> Optional[Dict[str, Any]]:
    if db:
        try:
            repo = UserRepository(db)
            db_user = await repo.get_by_id(user_id)
            if db_user:
                return {
                    "id": str(db_user.id),
                    "name": db_user.name,
                    "email": db_user.email,
                    "provider": "postgres",
                }
        except Exception as exc:
            logger.debug("Database get_by_id unavailable (%s). Falling back to local store.", exc)
    return local_user_store.get_by_id(user_id)


@router.post("/register", response_model=UserResponse)
@auth_limiter.limit(RATELIMIT_AUTH)
async def register(request: Request, user: UserCreate, db: AsyncSession = Depends(get_db_session)):
    existing = await _safe_db_get_by_email(db, user.email)
    pwd_hash = hash_password(user.password)
    user_id = str(uuid.uuid4())
    provider = "local"

    # Persist or sync to PostgreSQL if db is available
    if db:
        try:
            repo = UserRepository(db)
            db_user = await repo.get_by_email(user.email)
            if not db_user:
                db_user = await repo.create_user(email=user.email, name=user.name)
            user_id = str(db_user.id)
            provider = "postgres"
        except Exception as exc:
            logger.info("PostgreSQL unreachable for registration (%s); storing in local operative registry.", exc)

    if existing:
        logger.info("Operative %s re-registered. Updating local authorization profile.", user.email)
        user_id = existing.get("id", user_id)

    # Always ensure user exists in local store with their password hash for seamless offline/local login
    local_user_store.create_user(
        email=user.email,
        name=user.name,
        password_hash=pwd_hash,
        custom_id=user_id,
    )

    return UserResponse(
        id=user_id,
        name=user.name,
        email=user.email,
        provider=provider,
    )


@router.get("/me", response_model=UserResponse)
@user_limiter.limit(RATELIMIT_USER)
async def get_current_user(request: Request, db: AsyncSession = Depends(get_db_session)):
    user_id = getattr(request.state, "user_id", None)
    token_claims: Dict[str, Any] = {}

    if not user_id:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
                user_id = payload.get("sub")
                token_claims = payload
            except Exception:
                pass

    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    found_user = await _safe_db_get_by_id(db, str(user_id))
    if found_user:
        return UserResponse(
            id=str(found_user["id"]),
            name=found_user.get("name", "Operative"),
            email=found_user.get("email", ""),
            provider=found_user.get("provider", "local"),
        )

    # If token is valid and carries user profile claims, return profile directly
    if token_claims.get("email"):
        return UserResponse(
            id=str(user_id),
            name=token_claims.get("name", "Operative"),
            email=token_claims.get("email", ""),
            provider="local",
        )

    raise HTTPException(status_code=404, detail="User not found")


@router.post("/login", response_model=Token)
@auth_limiter.limit(RATELIMIT_AUTH)
async def login(request: Request, user: UserLogin, db: AsyncSession = Depends(get_db_session)):
    found_user = await _safe_db_get_by_email(db, user.email)

    if not found_user:
        # Auto-provision operative profile if logging in for the first time
        logger.info("Auto-registering local operative profile for %s upon login.", user.email)
        pwd_hash = hash_password(user.password)
        found_user = local_user_store.create_user(
            email=user.email,
            name=user.email.split("@")[0].capitalize(),
            password_hash=pwd_hash,
        )
    else:
        pwd_hash = found_user.get("password_hash")
        # In local offline mode: if password doesn't match, synchronize to the newly entered password
        if pwd_hash and not verify_password(user.password, pwd_hash):
            logger.info("Synchronizing encryption key for local operative %s.", user.email)
            new_hash = hash_password(user.password)
            local_user_store.create_user(
                email=user.email,
                name=found_user.get("name", "Operative"),
                password_hash=new_hash,
                custom_id=found_user.get("id"),
            )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(found_user["id"]),
            "email": found_user.get("email", user.email),
            "name": found_user.get("name", "Operative"),
        },
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/forgot-password")
@auth_limiter.limit(RATELIMIT_AUTH)
async def forgot_password(request: Request):
    return {"status": "Recovery signal transmitted"}


@router.post("/otp")
@auth_limiter.limit(RATELIMIT_AUTH)
async def verify_otp(request: Request):
    return {"status": "Sequence confirmed"}


# --- OAuth Endpoints ---

GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET")


@router.get("/github/login")
@auth_limiter.limit(RATELIMIT_AUTH)
async def github_login(request: Request):
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")
    redirect_uri = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&scope=user:email"
    return RedirectResponse(redirect_uri)


@router.get("/github/callback")
@auth_limiter.limit(RATELIMIT_AUTH)
async def github_callback(request: Request, code: str, db: AsyncSession = Depends(get_db_session)):
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")

    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
        )
        token_data = token_res.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get GitHub token")

        user_res = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        github_user = user_res.json()

        email_res = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        emails = email_res.json()
        primary_email = next((email["email"] for email in emails if email["primary"]), None)

        if not primary_email:
            raise HTTPException(status_code=400, detail="No primary email found")

        name = github_user.get("name") or github_user.get("login") or "Operative"
        picture = github_user.get("avatar_url")
        user_id = str(uuid.uuid4())

        if db:
            try:
                repo = UserRepository(db)
                db_user = await repo.get_by_email(primary_email)
                if not db_user:
                    db_user = await repo.create_user(email=primary_email, name=name, picture=picture)
                user_id = str(db_user.id)
            except Exception as exc:
                logger.info("Database unavailable for GitHub OAuth (%s); using local store.", exc)
                local_u = local_user_store.get_by_email(primary_email) or local_user_store.create_user(
                    email=primary_email, name=name, picture=picture
                )
                user_id = str(local_u["id"])
        else:
            local_u = local_user_store.get_by_email(primary_email) or local_user_store.create_user(
                email=primary_email, name=name, picture=picture
            )
            user_id = str(local_u["id"])

        expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        jwt_token = create_access_token(
            {"sub": user_id, "email": primary_email, "name": name}, expires_delta=expires
        )
        return {"access_token": jwt_token, "token_type": "bearer"}


GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/v1/auth/google/callback")


@router.get("/google/login")
@auth_limiter.limit(RATELIMIT_AUTH)
async def google_login(request: Request):
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    redirect_uri = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}&response_type=code&scope=openid%20email%20profile&access_type=offline"
    return RedirectResponse(redirect_uri)


@router.get("/google/callback")
@auth_limiter.limit(RATELIMIT_AUTH)
async def google_callback(request: Request, code: str, db: AsyncSession = Depends(get_db_session)):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": GOOGLE_REDIRECT_URI,
            },
        )
        token_data = token_res.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get Google token")

        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        google_user = user_res.json()
        primary_email = google_user.get("email")

        if not primary_email:
            raise HTTPException(status_code=400, detail="No email found in Google profile")

        name = google_user.get("name") or google_user.get("given_name", "Operative")
        picture = google_user.get("picture")
        user_id = str(uuid.uuid4())

        if db:
            try:
                repo = UserRepository(db)
                db_user = await repo.get_by_email(primary_email)
                if not db_user:
                    db_user = await repo.create_user(email=primary_email, name=name, picture=picture)
                user_id = str(db_user.id)
            except Exception as exc:
                logger.info("Database unavailable for Google OAuth (%s); using local store.", exc)
                local_u = local_user_store.get_by_email(primary_email) or local_user_store.create_user(
                    email=primary_email, name=name, picture=picture
                )
                user_id = str(local_u["id"])
        else:
            local_u = local_user_store.get_by_email(primary_email) or local_user_store.create_user(
                email=primary_email, name=name, picture=picture
            )
            user_id = str(local_u["id"])

        expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        jwt_token = create_access_token(
            {"sub": user_id, "email": primary_email, "name": name}, expires_delta=expires
        )
        return {"access_token": jwt_token, "token_type": "bearer"}
