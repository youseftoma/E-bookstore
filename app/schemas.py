from pydantic import BaseModel, ConfigDict, EmailStr,PositiveInt, condecimal
from typing import Literal
from datetime import datetime
from decimal import Decimal

from app import models


# token

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: str


# user

class UserBase(BaseModel):
    email: EmailStr
    role: Literal["admin","user"]

class CreateUser(UserBase):
    phone : str
    region: str
    hashed_password: str

class ChangePassword(BaseModel):
    password: str
    new_password: str

class ResetPassword(BaseModel):
    email: EmailStr
    phone : str
    region: str
    new_password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UserAdminResponse(UserBase):
    token: str
    verify_gmail: bool
    phone : str
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# comments
class CreateComment(BaseModel):
    book_id: int
    content: str

class UpdateComment(BaseModel):
    content: str

class CommentResponse(BaseModel):
    user: UserResponse
    content: str
    likes: int
    id: int
    created_at: datetime

#likes

class CreateLIke(BaseModel):
    object_id: int
    vote: Literal["upvote","remove"]


# book

class BookBase(BaseModel):
    name: str
    author: str
    description: str
    categories: list
    price: condecimal(ge=0)

class CreateBook(BookBase):
    stock: PositiveInt 

class BookCreateResponse(BookBase):
    stock: condecimal(ge=0) 
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class BookResponse(BookBase):
    likes: int
    comments: list[CommentResponse]
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# orderitem

class OrderItemBase(BaseModel):
    order_id: int
    book_id: int
    quantity: int

class CreateOrderItem(OrderItemBase):
    pass

class UpdateOrderItem(BaseModel):
    quantity: PositiveInt

class OrderItemResponse(OrderItemBase):
    price: Decimal
    total_amount: Decimal
    id: int
    created_at: datetime
    book: BookCreateResponse

    model_config = ConfigDict(from_attributes=True)

# order

class CreateOrder(BaseModel):
    name: str

class OrderResponse(BaseModel):
    name: str
    status: models.OrderStatus
    user_id: int
    total_amount: Decimal
    id: int
    created_at: datetime
    user: UserResponse
    order_items: list[OrderItemResponse] 

    model_config = ConfigDict(from_attributes=True)

class Payment(BaseModel):
    address: str


# ban user
class CreateBanUser(BaseModel):
    user_id: int
    years : condecimal(ge=0)
    months: condecimal(ge=0)

class UpdateBanUser(BaseModel):
    years : condecimal(ge=0)
    months: condecimal(ge=0)

class BanUserResponse(BaseModel):
    email: EmailStr
    id: int
    banned_at: datetime
    banned_to: datetime
    model_config = ConfigDict(from_attributes=True)

