import os
from datetime import datetime, timedelta
from typing import Annotated
from fastapi import Depends, APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from app.database import SessionLocal

from app.models import User
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

crypt_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")
oauth2_bearer_optional = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)

class CreateUser(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserVerification(BaseModel):
    password: str
    new_password: str

class DeleteAccountRequest(BaseModel):
    password: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        "Create a new user account.\n\n"
        "• Requires a unique username and password.\n"
        "• Passwords are securely hashed before storage.\n"
        "• Does not automatically authenticate the user."
    )
)
async def create_user(db: db_dependency, user_create: CreateUser):
    create_user_model = User(
        username=user_create.username,
        hashed_password=crypt_context.hash(user_create.password)
    )
    db.add(create_user_model)
    db.commit()
    return {"message": "Registration Successful"}

@router.post(
    "/token",
    response_model=Token,
    summary="Authenticate user and issue access token",
    description=(
        "Authenticate a user using username and password and return a JWT access token.\n\n"
        "• Uses OAuth2 password flow.\n"
        "• Token is required for authenticated endpoints.\n"
        "• Token expiration is limited in duration."
    )
)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user")
    token = create_access_token(user.username, user.id, timedelta(minutes=30))
    return {"access_token": token, "token_type": "bearer"}

def authenticate_user(username: str, password: str, db):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not crypt_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id}
    expires = datetime.now() + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user_optional(token: Annotated[str | None, Depends(oauth2_bearer_optional)]):
    if token is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user_id = payload.get("id")
        if username is None or user_id is None:
            return None
        return {"username": username, "id": user_id}
    except JWTError:
        return None

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user_id = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
        return {"username": username, "id": user_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

user_dependency = Annotated[dict, Depends(get_current_user)]

@router.put(
    "/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change user password",
    description=(
        "Change the authenticated user's password.\n\n"
        "• Requires the current password for verification.\n"
        "• A new password must be provided.\n"
        "• Authentication is required.\n"
    )
)
async def change_password(user_verification: UserVerification, db: db_dependency, user=Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    user_model = db.query(User).filter(User.id == user.get("id")).first()

    if not crypt_context.verify(user_verification.password, user_model.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
    user_model.hashed_password = crypt_context.hash(user_verification.new_password)
    db.add(user_model)
    db.commit()

@router.delete(
    "/delete",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user account",
    description=(
        "Permanently delete the authenticated user's account.\n\n"
        "• Requires password confirmation.\n"
        "• Authentication is required.\n"
        "• This action is irreversible.\n"
        "• All user-related data will be removed."
    )
)
async def delete_user(db: db_dependency, body: DeleteAccountRequest, user: dict = Depends(get_current_user)):
    user_model = db.query(User).filter(User.id == user["id"]).first()
    if not user_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not crypt_context.verify(body.password, user_model.hashed_password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect password")
    db.delete(user_model)
    db.commit()