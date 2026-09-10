"""
Authentication — JWT-based role authentication.
Roles: admin (Transportation Planner) | driver
Passwords are hashed with bcrypt. Default demo credentials:
  admin / admin123
  driver / driver123
"""
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

router = APIRouter()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "school-bus-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480   # 8 hours

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Simple in-memory user store for demo (production: use DB)
USERS_DB = {
    "admin": {
        "username": "admin",
        "full_name": "Transportation Planner",
        "email": "admin@schoolbus.local",
        "hashed_password": pwd_context.hash("admin123"),
        "role": "admin",
        "disabled": False,
    },
    "driver": {
        "username": "driver",
        "full_name": "Bus Driver",
        "email": "driver@schoolbus.local",
        "hashed_password": pwd_context.hash("driver123"),
        "role": "driver",
        "disabled": False,
    },
}


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str
    full_name: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class User(BaseModel):
    username: str
    full_name: str
    email: str
    role: str
    disabled: bool


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_user(username: str) -> Optional[dict]:
    return USERS_DB.get(username)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return current_user


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/token", response_model=Token)
async def login_form(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user["role"],
        username=user["username"],
        full_name=user["full_name"],
    )


@router.post("/login", response_model=Token)
async def login_json(req: LoginRequest):
    user = authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user["role"],
        username=user["username"],
        full_name=user["full_name"],
    )


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "full_name": current_user["full_name"],
        "email": current_user["email"],
        "role": current_user["role"],
    }
