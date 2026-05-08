from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Numeric,Boolean,func, ForeignKey,Enum,select
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from decimal import Decimal
from enum import Enum as pyEnum
import secrets
from app.database import Base,engine


class OrderStatus(str, pyEnum):
    PENDING = "pending"
    ORDERED = "ordered"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    
    def __str__(self):
        return super().__str__()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True,index=True)
    email: Mapped[str] = mapped_column(unique=True,index=True)
    token: Mapped[str] = mapped_column(default=lambda: secrets.token_urlsafe(16))
    verify_gmail: Mapped[bool] = mapped_column(Boolean, default=False)
    phone: Mapped[str] = mapped_column(String(20), nullable= False,index=True)
    hashed_password: Mapped[str]
    role: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    orders: Mapped[list["Order"]] = relationship(back_populates="user",
        cascade="all, delete-orphan")


class BanUser(Base):
    __tablename__ = "banned_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True,index=True)
    banned_at: Mapped[datetime] = mapped_column(server_default=func.now())
    banned_to: Mapped[datetime] = mapped_column(nullable=False)


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True,index=True)
    name: Mapped[str]
    author: Mapped[str]
    categories: Mapped[list] = mapped_column(JSONB)
    description: Mapped[str]
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    stock: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="book",cascade="all, delete-orphan")
    comments: Mapped[list["Comment"]] = relationship(back_populates="book", cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True,index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id",ondelete="CASCADE"))
    name: Mapped[str]
    address: Mapped[str] = mapped_column(nullable=True)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2),nullable=False,server_default="0.00")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="orders")
    order_items: Mapped[list["OrderItem"]
        ] = relationship(back_populates="order",cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True,index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id",ondelete="CASCADE"))
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id",ondelete="CASCADE"))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int]
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    order: Mapped["Order"] = relationship(back_populates="order_items")
    book: Mapped["Book"] = relationship(back_populates="order_items")


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True,index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id",ondelete="CASCADE"))
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id",ondelete="CASCADE"))
    content: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
    user: Mapped["User"] = relationship()
    book: Mapped["Book"] = relationship("Book", back_populates="comments")

    @property
    def likes(self) -> int:
        # This calculates the count on the fly when Pydantic accesses the field
        from sqlalchemy.orm import object_session
        session = object_session(self)
        if session:
            return session.scalar(
                select(func.count(Comment_Like.comment_id))
                .filter(Comment_Like.comment_id == self.id)
            ) or 0
        return 0
    
    
class Book_Like(Base):
    __tablename__ = "book_likes"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id",ondelete="CASCADE"), primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id",ondelete="CASCADE"), primary_key=True)

class Comment_Like(Base):
    __tablename__ = "comments_likes"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id",ondelete="CASCADE"), primary_key=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id",ondelete="CASCADE"), primary_key=True)
