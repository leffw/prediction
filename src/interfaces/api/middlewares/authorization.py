from src.configs import API_JWT_SECRET_KEY
from fastapi import Request, HTTPException
import jwt


def isAuthorization(request: Request) -> Request:
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not (token):
        raise HTTPException(401)

    try:
        request.data = jwt.decode(
            jwt=token, key=API_JWT_SECRET_KEY, algorithms=["HS256"])
    except:
        raise HTTPException(401)
    
    if (request.data["blocked"] == True):
        raise HTTPException(401)
    else:
        return request