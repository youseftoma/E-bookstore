from fastapi import APIRouter, HTTPException, status, Depends, Request
from sqlalchemy.orm import Session

from .. import models, schemas, database, oauth2, utils
from ..limiter import limiter

route = APIRouter(
    prefix="/order",
    tags=["orders"]
)

# Admin router
adminroute = APIRouter(
    prefix="/admins/order",
    tags=["orders", "admins"],
    dependencies=[Depends(utils.admin_only)])


@route.get("/me", response_model=list[schemas.OrderResponse])
@limiter.limit("10/minute")
def get_orders_of_user(request: Request,limit: int = 10, skip: int = 0, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):

    orders = (db.query(models.Order).filter(models.Order.user_id == current_user.id)
              .offset(skip).limit(limit).all())
    return orders


@route.post("/", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def create_order(request: Request,create_order: schemas.CreateOrder, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):

    order = models.Order(user_id=current_user.id,
                         name=create_order.name,
                         status=models.OrderStatus.PENDING)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@route.get("/{id}", response_model=schemas.OrderResponse)
@limiter.limit("10/minute")
def get_order(request: Request,id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    order = utils.get_order_or_404(id, db).first()
    utils.verify_owner_or_403(order.user_id, db, current_user)
    return order


@route.put("/{id}", response_model=schemas.OrderResponse)
@limiter.limit("5/minute")
def update_order(request: Request,id: int, update_order: schemas.CreateOrder, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):

    order = utils.get_order_or_404(id, db).first()
    utils.verify_owner_or_403(order.user_id, db, current_user)
    order.name = update_order.name
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@route.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
def delete_order(request: Request,id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):

    order = utils.get_order_or_404(id, db).first()
    utils.verify_owner_or_403(order.user_id, db, current_user)
    db.delete(order)
    db.commit()


@route.put("/payment/{id}", response_model=schemas.OrderResponse)
@limiter.limit("4/minute")
def ordering_the_order(request: Request,id: int, payment: schemas.Payment, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):

    order = utils.get_order_or_404(id, db).first()
    if order.status == models.OrderStatus.ORDERED or order.status == models.OrderStatus.SHIPPED or order.status == models.OrderStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"this order is already {order.status}")
    utils.verify_owner_or_403(order.user_id, db, current_user)
    order_items = order.order_items
    for order_item in order_items:
        if order_item.quantity > order_item.book.stock:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"now there isnt  {order_item.quantity} quantity from the book {order_item.book.name} there is only {order_item.book.stock} stock")
        order_item.book.stock -= order_item.quantity
    order.status = models.OrderStatus.ORDERED
    order.address = payment.address
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@route.put("/payment/cancel/{id}", response_model=schemas.OrderResponse)
@limiter.limit("4/minute")
def canceling_the_order(request: Request,id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):

    order = utils.get_order_or_404(id, db).first()
    if order.status == models.OrderStatus.CANCELLED or order.status == models.OrderStatus.PENDING or order.status == models.OrderStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"this order is already {order.status}")
    utils.verify_owner_or_403(order.user_id, db, current_user)
    order_items = order.order_items
    for order_item in order_items:
        if order_item.quantity > order_item.book.stock:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"now this isnt  {order_item.quantity} quantity from the book {order_item.book.name} this is only {order_item.book.stock} stock")
        order_item.book.stock += order_item.quantity
    order.status = models.OrderStatus.CANCELLED
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@adminroute.get("/ordered", response_model=list[schemas.OrderResponse])
def get_ordered_orders(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    order = db.query(models.Order).filter(
        models.Order.status == models.OrderStatus.ORDERED).all()
    return order


@adminroute.get("/shiping", response_model=list[schemas.OrderResponse])
def get_shiping_orders(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    order = db.query(models.Order).filter(
        models.Order.status == models.OrderStatus.SHIPPED).all()
    return order


@adminroute.get("/cancel", response_model=list[schemas.OrderResponse])
def get_canceled_orders(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    order = db.query(models.Order).filter(
        models.Order.status == models.OrderStatus.CANCELLED).all()
    return order


@adminroute.get("/completing", response_model=list[schemas.OrderResponse])
def get_completed_orders(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    order = db.query(models.Order).filter(
        models.Order.status == models.OrderStatus.COMPLETED).all()
    return order


@adminroute.put("/shiping/{id}", response_model=schemas.OrderResponse)
def make_the_order_shiping(id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):

    order = utils.get_order_or_404(id, db).first()
    if order.status == models.OrderStatus.CANCELLED or order.status == models.OrderStatus.PENDING or order.status == models.OrderStatus.SHIPPED or order.status == models.OrderStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"this order is already {order.status}")
    order.status = models.OrderStatus.SHIPPED
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@adminroute.put("/completing/{id}", response_model=schemas.OrderResponse)
def make_the_order_completing(id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):

    order = utils.get_order_or_404(id, db).first()
    if order.status == models.OrderStatus.CANCELLED or order.status == models.OrderStatus.PENDING or order.status == models.OrderStatus.ORDERED or order.status == models.OrderStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"this order is already {order.status}")
    order.status = models.OrderStatus.COMPLETED
    db.add(order)
    db.commit()
    db.refresh(order)
    return order
