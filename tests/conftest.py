from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from decimal import Decimal
from datetime import datetime, timedelta

from app.main import app
from app.config import settings
from app.database import get_db, Base
from app.oauth2 import create_access_token
from app.schemas import BanUserResponse, UserAdminResponse ,BookCreateResponse, OrderResponse, OrderItemResponse
from app import models

SQLALCHEMY_DATABASE_URL = f'{settings.SQLALCHEMY_DATABASE_URL}_test'

engine = create_engine(SQLALCHEMY_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# test without authentication
@pytest.fixture()
def client(session):
    def override_get_db():

        try:
            yield session
        finally:
            session.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)


# test with authentication for user1 admin
@pytest.fixture()
def test_admin_user(client,session):
    user_data ={
            "email": "admin@example.com",
            "role": "admin",
            "phone": "01011758453",
            "region": "EG",
            "hashed_password": "fake_hashed_password_1"
        }
    res = client.post("/users/",json=user_data)
    assert res.status_code == 201
    new_user_data = res.json()
    user = session.query(models.User).filter(models.User.id == new_user_data["id"]).first()
    user.verify_gmail = True
    session.commit()
    session.refresh(user)
    new_user_data = res.json()
    new_user_data["hashed_password"] = user_data["hashed_password"]
    new_user_data["verify_gmail"] = user.verify_gmail
    new_user_data["token"] = user.token
    new_user_data["phone_number"] = user_data["phone"]
    new_user_data["region"] = user_data["region"]
    return new_user_data

@pytest.fixture()
def token_user1(test_admin_user):
    return create_access_token({"user_id": test_admin_user["id"]})

@pytest.fixture()
def authorized_client_user1(client, token_user1):
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token_user1}"
    }
    return client

# test with authentication for user2 customer
@pytest.fixture()
def test_verify_user(client, session):
    user_data ={
            "email": "customer@example.com",
            "role": "user",
            "phone": "01211758453",
            "region": "EG",
            "hashed_password": "fake_hashed_password_2"
        }
    res = client.post("/users/",json=user_data)
    assert res.status_code == 201
    new_user_data = res.json()

    user = session.query(models.User).filter(models.User.id == new_user_data["id"]).first()
    user.verify_gmail = True
    session.commit()
    session.refresh(user)
    new_user_data["hashed_password"] = user_data["hashed_password"]
    new_user_data["verify_gmail"] = user.verify_gmail
    new_user_data["token"] = user.token
    new_user_data["phone_number"] = user_data["phone"]
    new_user_data["region"] = user_data["region"]
    return new_user_data

@pytest.fixture()
def token_user2(test_verify_user):
    return create_access_token({"user_id": test_verify_user["id"]})

@pytest.fixture()
def authorized_client_user2(client, token_user2):
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token_user2}"
    }
    return client

# test with authentication for user3 unverified user
@pytest.fixture()
def test_unverified_user(client, session):
    user_data ={
            "email": "unverified@example.com",
            "role": "user",
            "phone": "01211758453",
            "region": "EG",
            "hashed_password": "fake_hashed_password_3"
        }
    res = client.post("/users/",json=user_data)
    assert res.status_code == 201
    new_user_data = res.json()
    user = session.query(models.User).filter(models.User.id == new_user_data["id"]).first()
    user.verify_gmail = False
    new_user_data["hashed_password"] = user_data["hashed_password"]
    new_user_data["verify_gmail"] = user.verify_gmail
    new_user_data["token"] = user.token
    new_user_data["phone_number"] = user_data["phone"]
    new_user_data["region"] = user_data["region"]
    new_user_data["verify_gmail"] = False
    return new_user_data

# users with different roles and verification status for testing various scenarios 
@pytest.fixture()
def test_users(session):
    users = [
        models.User(
            email="admin1@example.com",
            verify_gmail=True,
            phone="+1234567890",
            hashed_password="fake_hashed_password_1",
            role="admin"
        ),
        models.User(
            email="customer1@example.com",
            verify_gmail=True,
            phone="+1987654321",
            hashed_password="fake_hashed_password_2",
            role="user"
        ),
        models.User(
            email="unverified1@example.com",
            verify_gmail=False,
            phone="+1555000111",
            hashed_password="fake_hashed_password_3",
            role="user"
        )
    ]
    session.add_all(users)
    session.commit()
    for user in users:
        session.refresh(user)
    users = [UserAdminResponse.model_validate(user).model_dump() for user in users]
    return users


#banned user for testing access restrictions and error handling related to banned accounts
@pytest.fixture()
def test_banned_user(client, session):
    user_data = {
        "email": "banned@example.com",
        "role": "user",
        "phone": "01511758453",
        "region": "EG",
        "hashed_password": "fake_hashed_password_ban"
    }
    res = client.post("/users/", json=user_data)
    assert res.status_code == 201
    new_user_data = res.json()
    user = session.query(models.User).filter(models.User.id == new_user_data["id"]).first()
    new_user_data["hashed_password"] = user_data["hashed_password"]
    new_user_data["verify_gmail"] = user.verify_gmail
    new_user_data["token"] = user.token
    new_user_data["phone_number"] = user_data["phone"]
    new_user_data["region"] = user_data["region"]

    ban_entry = models.BanUser(
        email=user_data["email"],
        banned_to=datetime.now() + timedelta(days=1)
    )
    session.add(ban_entry)
    session.commit()
    session.refresh(ban_entry)
    ban = BanUserResponse.model_validate(ban_entry).model_dump()
    return {
        "user": new_user_data,
        "ban": ban
    }

@pytest.fixture()
def test_banned_user_expired(client, session):
    user_data = {
        "email": "banned1@example.com",
        "role": "user",
        "phone": "01511758453",
        "region": "EG",
        "hashed_password": "fake_hashed_password_ban1"
    }
    res = client.post("/users/", json=user_data)
    assert res.status_code == 201
    new_user_data = res.json()

    user = session.query(models.User).filter(models.User.id == new_user_data["id"]).first()
    new_user_data["hashed_password"] = user_data["hashed_password"]
    new_user_data["verify_gmail"] = user.verify_gmail
    new_user_data["token"] = user.token
    new_user_data["phone_number"] = user_data["phone"]
    new_user_data["region"] = user_data["region"]
    ban_entry = models.BanUser(
        email=user_data["email"],
        banned_to=datetime.now() - timedelta(days=1)
    )
    session.add(ban_entry)
    session.commit()
    session.refresh(ban_entry)
    ban = BanUserResponse.model_validate(ban_entry).model_dump()
    return {
        "user": new_user_data,
        "ban": ban
    }


@pytest.fixture()
def test_banned_users(session):
    banned_users = [
        models.BanUser(
            email="banned1@example.com",
            banned_to= datetime.now() + timedelta(days=1)
        ),
        models.BanUser(
            email="banned2@example.com",
            banned_to=datetime.now() - timedelta(days=1)
        ),
        models.BanUser(
            email="banned3@example.com",
            banned_to=datetime.now() + timedelta(days=1)
        )
    ]
    session.add_all(banned_users)
    session.commit()
    for banned_user in banned_users:
        session.refresh(banned_user)
    banned_users = [BanUserResponse.model_validate(bu).model_dump() for bu in banned_users]
    return banned_users

# book for testing book-related operations and order processing
@pytest.fixture()
def test_book(session):
    book = models.Book(
        name="Test Book",
        author="Test Author",
        categories=["Fiction", "Science"],
        description="Test book description",
        price=Decimal("29.99"),
        stock=100
    )
    session.add(book)
    session.commit()
    session.refresh(book)
    book = BookCreateResponse.model_validate(book).model_dump()
    return book

# multiple books for testing pagination, filtering, and sorting functionalities in book-related endpoints
@pytest.fixture()
def test_books(session):
    books_data = [
        models.Book(
            name="Book One",
            author="Author One",
            categories=["Fiction"],
            description="First test book",
            price=Decimal("15.99"),
            stock=50
        ),
        models.Book(
            name="Book Two",
            author="Author Two",
            categories=["Science", "Technology"],
            description="Second test book",
            price=Decimal("25.99"),
            stock=30
        ),
        models.Book(
            name="Book Three",
            author="Author Three",
            categories=["History"],
            description="Third test book",
            price=Decimal("19.99"),
            stock=75
        ),
    ]
    session.add_all(books_data)
    session.commit()
    for book in books_data:
        session.refresh(book)
    books = [BookCreateResponse.model_validate(book).model_dump() for book in books_data]
    
    return books
    


# order and order item for testing order-related operations
@pytest.fixture()
def test_order(session, test_verify_user, test_book):
    order = models.Order(
        user_id=test_verify_user["id"],
        name="Test Order",
        status=models.OrderStatus.PENDING,
        total_amount=Decimal("0.00")
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    order = OrderResponse.model_validate(order).model_dump()
    return order

@pytest.fixture()
def test_orders(session,test_verify_user,test_admin_user):
    orders = [
        models.Order(
        user_id=test_verify_user["id"],
        name="Test Order 1",
        status=models.OrderStatus.PENDING,
        total_amount=Decimal("0.00")
        ),
        models.Order(
        user_id=test_verify_user["id"],
        name="Test Order 2",
        status=models.OrderStatus.PENDING,
        total_amount=Decimal("0.00")
        ),
       models.Order(
        user_id=test_admin_user["id"],
        name="Test Order 3",
        status=models.OrderStatus.COMPLETED,
        total_amount=Decimal("0.00")
        )
    ]
    session.add_all(orders)
    session.commit()
    for order in orders:
        session.refresh(order)
    orders = [OrderResponse.model_validate(order).model_dump() for order in orders]
    return orders


@pytest.fixture()
def test_order_item(session, test_order, test_book):
    price = Decimal(str(test_book["price"])) 
    order_item = models.OrderItem(
        order_id=test_order["id"],
        book_id=test_book["id"],
        price=price,
        quantity=2,
        total_amount=price * 2
    )
    session.add(order_item)
    session.commit()
    session.refresh(order_item)
    order_item = OrderItemResponse.model_validate(order_item).model_dump()
    return order_item


@pytest.fixture()
def test_order_items(session,test_books,test_orders):
    price_0 = Decimal(str(test_books[0]["price"])) 
    price_1 = Decimal(str(test_books[1]["price"])) 
    order_items = [
        models.OrderItem(
        order_id=test_orders[0]["id"],
        book_id=test_books[0]["id"],
        price=price_0,
        quantity=2,
        total_amount= price_0 * 2
        ),
        models.OrderItem(
        order_id=test_orders[0]["id"],
        book_id=test_books[1]["id"],
        price=price_1,
        quantity=3,
        total_amount=price_1 * 3
        ),
        models.OrderItem(
        order_id=test_orders[2]["id"],
        book_id=test_books[1]["id"],
        price=price_1,
        quantity=1,
        total_amount=price_1 * 1
        )
    ]
    for order_item in order_items:
        order = session.query(models.Order).filter(models.Order.id == order_item.order_id).first()
        order.total_amount +=  order_item.total_amount
    session.add_all(order_items)
    session.commit()
    for order_item in order_items:
        session.refresh(order_item)
    order_items = [OrderItemResponse.model_validate(order_item).model_dump() for order_item in order_items]
    return order_items


@pytest.fixture()
def test_comment(session, test_verify_user, test_book):
    comment = models.Comment(
        user_id=test_verify_user["id"],
        book_id=test_book["id"],
        content="This is a test comment."
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return {
        "id": comment.id,
        "user_id": comment.user_id,
        "book_id": comment.book_id,
        "content": comment.content
    }

@pytest.fixture()
def test_like(session, test_verify_user, test_book):
    like = models.Book_Like(
        user_id=test_verify_user["id"],
        book_id=test_book["id"]
    )
    session.add(like)
    session.commit()
    session.refresh(like)
    return like

@pytest.fixture()
def test_comment_like(session, test_verify_user, test_comment):
    comment_like = models.Comment_Like(
        user_id=test_verify_user["id"],
        comment_id=test_comment["id"]
    )
    session.add(comment_like)
    session.commit()
    session.refresh(comment_like)
    return comment_like