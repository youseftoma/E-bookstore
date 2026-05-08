from  jose  import  JWTError,jwt
from datetime import datetime, timedelta
from  fastapi import Depends, status, HTTPException 
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .config import settings

from . import schemas,database,models


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl='login', 
    scheme_name="JWT_Access"
)

SECRET_KEY = settings.SECRET_KEY
ALGORITHM= settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_TIME = settings.ACCESS_TOKEN_EXPIRE_TIME

#create token

def create_access_token(data: dict):
    to_encode = data.copy()
    access_token_expire_time = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_TIME)
    to_encode.update({"exp": access_token_expire_time})
    return jwt.encode(to_encode, SECRET_KEY, ALGORITHM)

def verify_access_token(token, exc):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id=payload.get("user_id")
        if not id:
            raise exc
        return schemas.TokenData(id = str(id))
    except JWTError:
        raise exc

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",headers={"WWW-Authenticate":"Bearer"})
    token_data = verify_access_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.id == token_data.id).first()
    if not user: 
        raise credentials_exception
    return user
