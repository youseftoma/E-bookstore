from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..  import models,schemas,database,utils,oauth2
from ..limiter import limiter

route = APIRouter(tags=["authentication"])


# login

@route.post("/login", response_model=schemas.Token)
@limiter.limit("10/minute")
def login(request: Request,user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid credentials")
    if not utils.verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid credentials")
    if user.verify_gmail == False :
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="hasnt Verificate the email")
    utils.verify_not_banned_or_403(user_credentials.username, db)
    token = oauth2.create_access_token(data={"user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}
