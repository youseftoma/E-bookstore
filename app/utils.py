from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from datetime import datetime
import phonenumbers

from app import models, oauth2

# Hash a password
def hash_password(password):
    hashed = bcrypt.hash(password)
    return hashed

# Verify a password
def verify_password(password,hashed_password):
    is_valid = bcrypt.verify(password, hashed_password)
    return is_valid

def validate_phone(phone: str, region: str = "EG") -> str:
    try:
        # Parse the number with a default region (e.g., Egypt "EG")
        parsed = phonenumbers.parse(phone, region)

        # Check if it's a valid number
        if phonenumbers.is_valid_number(parsed):
            # Format to E.164 standard (+201234567890)
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        else:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail="Invalid phone number")

    except phonenumbers.NumberParseException:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail="Invalid format")




# Admin-only dependency
def admin_only(current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource"
        )
    return current_user

def verify_owner_or_403(input_id:int, db: Session, current_user: models.User):
    user = db.query(models.User).filter(models.User.id == input_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"the user of id {input_id} not exist")
    if current_user.role == "admin":
        pass
    elif user.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource")

def verify_not_banned_or_403(email:str, db: Session):
    verify_user = db.query(models.BanUser).filter(models.BanUser.email == email).first()
    if verify_user:
        if verify_user.banned_to > datetime.now():
            raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"the email {verify_user.email} is banned to {verify_user.banned_to}")
        elif verify_user.banned_to < datetime.now():
            db.delete(verify_user)
            db.commit()

def get_book_or_404(input_id:int,db: Session ):
    book = db.query(models.Book).filter(models.Book.id == input_id)
    if not book.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"the book with id {input_id} not exist")
    return book

def get_order_or_404(input_id:int,db: Session ):
    order = db.query(models.Order).filter(models.Order.id == input_id)
    if not order.first() :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"the order with id {input_id} not exist")
    return order

def get_orderitem_or_404(input_id:int,db: Session ):
    orderitem = db.query(models.OrderItem).filter(models.OrderItem.id == input_id)
    if not orderitem.first() :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"the orderitem with id {input_id} not exist")
    return orderitem

def get_comment_or_404(input_id:int,db: Session ):
    comment = db.query(models.Comment).filter(models.Comment.id == input_id)
    if not comment.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"the comment with id {input_id} not exist")
    return comment