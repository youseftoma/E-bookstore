from fastapi import APIRouter, HTTPException, status, Depends,Request
from sqlalchemy.orm import Session
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Optional

from .. import models, schemas, database, utils, oauth2,notifications
from ..limiter import limiter
from ..config import settings

route = APIRouter(
    prefix="/users",
    tags=["users"])

# Admin router
adminroute = APIRouter(
    prefix="/admins/users",
    tags=["users", "admins"],
    dependencies=[Depends(utils.admin_only)])

banroute = APIRouter(
    prefix="/admins/ban/users",
    tags=["users", "admins"],
    dependencies=[Depends(utils.admin_only)])


# create user

@route.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def create_user(request: Request,create_user: schemas.CreateUser, db: Session = Depends(database.get_db)):
    
    utils.verify_not_banned_or_403(create_user.email,db)
    phone = utils.validate_phone(create_user.phone,create_user.region)
    user_data = create_user.dict()
    user_data["hashed_password"] = utils.hash_password(
        create_user.hashed_password)
    user_data["phone"] = phone
    user_data.pop("region")
    if create_user.email == db.query(models.User).filter(models.User.email == create_user.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"the email {create_user.email} is already exist")
    user = models.User(**user_data)
    
    if settings.TESTING == True:
        user.verify_gmail = True
        pass
    elif not notifications.send_verify_gmail(create_user.email,f"http://127.0.0.1:8000/users/verify_gmail/{user.token}") :
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"there is some problem in the server try again later")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@route.get("/verify_gmail/{token}")
@limiter.limit("5/minute")
def verify_user_gmail(request: Request,token:str, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.token == token).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Verification email successfully failed")
    if db.query(models.BanUser).filter(models.BanUser.email == user.email).first():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"the user with email {user.email} is banned")
    if user.verify_gmail == True:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"the user with email {user.email} has verification already")
    user.verify_gmail = True
    db.commit()
    return{"message": "Verification email successfully"}




@route.put("/reset_password")
@limiter.limit("5/minute")
def reset_password(request: Request,update_password: schemas.ResetPassword ,db: Session = Depends(database.get_db)):
    
    utils.verify_not_banned_or_403(update_password.email,db)
    user = db.query(models.User).filter(models.User.email == update_password.email).first()
    if  user == None or user.phone != utils.validate_phone(update_password.phone,update_password.region):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="invalid credentials")
    user.hashed_password = utils.hash_password(update_password.new_password)
    db.commit()

@route.put("/change_password")
@limiter.limit("5/minute")
def change_password(request: Request,update_password: schemas.ChangePassword ,db: Session = Depends(database.get_db)
                ,current_user: models.User = Depends(oauth2.get_current_user)):
    
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not utils.verify_password(update_password.password , user.hashed_password):
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail=f"the password {update_password.password} not True")
    user.hashed_password = utils.hash_password(update_password.new_password)
    db.commit()

# get profile


@route.get("/me", response_model=schemas.UserResponse)
@limiter.limit("5/minute")
def get_user_profile(request: Request,current_user: models.User = Depends(oauth2.get_current_user)):

    return current_user


# get users

@adminroute.get("/", response_model=list[schemas.UserAdminResponse])
def get_users(limit:int=10, skip:int=0, role:Optional[str]=None, db: Session = Depends(database.get_db)
              , current_user: models.User = Depends(oauth2.get_current_user)):
    query = db.query(models.User)
    if role:
        query = query.filter(models.User.role.contains(role))
    users = query.offset(skip).limit(limit).all()
    return users



# get by id


@adminroute.get("/{id}", response_model=schemas.UserAdminResponse)
def get_user(id: int, db: Session = Depends(database.get_db)
             , current_user: models.User = Depends(oauth2.get_current_user)):
    
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource"
        )
    
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"the user of id {id} not exist")

    return user

@adminroute.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_user(id:int ,db: Session = Depends(database.get_db)
                ,current_user: models.User = Depends(oauth2.get_current_user)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"the User with id {id} not exist")
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="you cant delete yourself")
    db.delete(user)
    db.commit()



@banroute.get("/",response_model=list[schemas.BanUserResponse])
def banned_users(limit:int=10, skip:int=0, role:Optional[str]=None,db: Session = Depends(database.get_db)
             ,current_user: models.User = Depends(oauth2.get_current_user)):
    
    query = db.query(models.BanUser)
    if role:
        query = query.filter(models.User.role.contains(role))
    users = query.offset(skip).limit(limit).all()
    return users



@banroute.post("/",response_model=schemas.BanUserResponse,status_code=status.HTTP_201_CREATED)
def ban_user(user_to_ban: schemas.CreateBanUser, db: Session = Depends(database.get_db)
             ,current_user: models.User = Depends(oauth2.get_current_user)):
    user = db.query(models.User).filter(models.User.id == user_to_ban.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"the User with id {user_to_ban.user_id} not exist")
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="you cant ban yourself")
    utils.verify_not_banned_or_403(user.email,db)
    future_date = datetime.now() + relativedelta(years=user_to_ban.years, months=user_to_ban.months)
    banned_user = models.BanUser(email = user.email,
                                 banned_to = future_date)
    db.add(banned_user)
    db.commit()
    db.refresh(banned_user)
    return banned_user

@banroute.put("/{id}",response_model=schemas.BanUserResponse)
def update_banned_user(id:int ,update_banned: schemas.UpdateBanUser ,db: Session = Depends(database.get_db)
                ,current_user: models.User = Depends(oauth2.get_current_user)):
    
    banned_user = db.query(models.BanUser).filter(models.BanUser.id == id).first()
    if not banned_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"the User with id {id} not exist")
    banned_user.banned_to = datetime.now() + relativedelta(years=update_banned.years
                                                           , months=update_banned.months)
    db.commit()
    return banned_user

@banroute.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_banned_user(id:int ,db: Session = Depends(database.get_db)
                ,current_user: models.User = Depends(oauth2.get_current_user)):
    banned_user = db.query(models.BanUser).filter(models.BanUser.id == id).first()
    if not banned_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"the banned_user with id {id} not exist")
    db.delete(banned_user)
    db.commit()



