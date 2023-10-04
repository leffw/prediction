from src.interfaces.api.middlewares.authorization import isAuthorization
from src.interfaces.api.schemas import UserSchema
from src.database import Balance, User
from src.configs import API_JWT_SECRET_KEY
from fastapi import APIRouter, HTTPException, Depends, Request
from time import time

import bcrypt
import jwt

router = APIRouter()

@router.post("/api/v1/create")
def create_account(data: UserSchema):
    username = data.username
    password = data.password
    if (User.select(User.id).where(User.username == username).exists() == True):
        raise HTTPException(409, "An account with the same username already exists.")
    else:
        hashed_password = bcrypt.hashpw(
            password=password.encode(), salt=bcrypt.gensalt()).decode()
        try:
            user = User.get_or_create(
                username=username, 
                password=hashed_password
            )[0]
            Balance.create(user=user.id)
            return { "message": "Account successfully created." }
        except:
            raise HTTPException(500)

@router.post("/api/v1/auth")
def auth_account(data: UserSchema):
    user = User.select().where(User.username == data.username)
    if (user.exists() == False):
        raise HTTPException(401)
    else:
        user = user.get()

    if (bcrypt.checkpw(password=data.password.encode(), hashed_password=user.password.encode()) == False):
        raise HTTPException(401)

    payload = { 
        "id":       str(user.id), 
        "blocked":  user.blocked,
        "verified": user.verified, 
        "is_admin": user.is_admin,
        "exp":      time() + 86400
    }
    token = jwt.encode(payload=payload, key=API_JWT_SECRET_KEY, algorithm="HS256")
    return { "token": token, "verified": user.verified, "blocked": user.blocked, "is_admin": user.is_admin, "expiry": payload["exp"] }

@router.get("/api/v1/balance")
def get_balance(request: Request = Depends(isAuthorization)):
    if (request.data["verified"] == False):
        raise HTTPException(401, "You cannot access this feature as your account has not been verified.")
    
    balance = Balance.select(Balance.balance).where(
        (Balance.user == request.data["id"])).get().balance
    return { "balance": balance }