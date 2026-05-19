from fastapi import APIRouter, status,Depends, Request
from sqlalchemy.orm import Session

from ..  import models,schemas,database,oauth2,utils
from ..limiter import limiter

route = APIRouter(
    prefix= "/orderitems",
    tags=["orderitems"]
          )


# Admin router
adminroute = APIRouter(
    prefix="/admins/orderitems",
    tags=["orderitems", "admins"],
    dependencies=[Depends(utils.admin_only)])



@route.post("/",response_model=schemas.OrderItemResponse,status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def create_orderitem(request: Request,create_orderitem: schemas.CreateOrderItem,db: Session = Depends(database.get_db)
                    ,current_user: models.User = Depends(oauth2.get_current_user)):
    book = utils.get_book_or_404(create_orderitem.book_id,db).first()
    order = utils.get_order_or_404(create_orderitem.order_id,db).first()
    price = book.price
    total_amount =create_orderitem.quantity * price
    orderitem = models.OrderItem(
        order_id=create_orderitem.order_id,
        book_id=create_orderitem.book_id,
        price=price,
        quantity=create_orderitem.quantity,
        total_amount=total_amount)
    order.total_amount += total_amount
    db.add(orderitem)
    db.commit()
    db.refresh(orderitem)
    return orderitem


@route.get("/{id}",response_model=schemas.OrderItemResponse)
@limiter.limit("10/minute")
def get_orderitem(request: Request,id:int ,db: Session = Depends(database.get_db)
                    ,current_user: models.User = Depends(oauth2.get_current_user)):
    orderitem = utils.get_orderitem_or_404(id,db).first()
    utils.verify_owner_or_403(orderitem.order.user_id,db,current_user)
    return orderitem

@route.put("/{id}",response_model=schemas.OrderItemResponse)
def update_orderitem(id:int ,update_orderitem: schemas.UpdateOrderItem, db: Session = Depends(database.get_db)
                    ,current_user: models.User = Depends(oauth2.get_current_user)):

    orderitem = utils.get_orderitem_or_404(id,db).first()
    order = utils.get_order_or_404(orderitem.order_id,db).first()
    utils.verify_owner_or_403(order.user_id,db,current_user)
    order.total_amount -= orderitem.total_amount
    orderitem.quantity = update_orderitem.quantity
    orderitem.total_amount = orderitem.quantity * orderitem.price
    order.total_amount += orderitem.total_amount
    db.add(orderitem)
    db.commit()
    db.refresh(orderitem)
    return orderitem    

@route.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
def delete_orderitem(request: Request,id:int ,db: Session = Depends(database.get_db)
                    ,current_user: models.User = Depends(oauth2.get_current_user)):
    
    orderitem = utils.get_orderitem_or_404(id,db).first()
    order = utils.get_order_or_404(orderitem.order_id,db).first()
    utils.verify_owner_or_403(order.user_id,db,current_user)
    order.total_amount -= orderitem.total_amount
    db.delete(orderitem)
    db.commit()   



@adminroute.get("/",response_model=list[schemas.OrderItemResponse])
def get_orderitems(limit:int=10, skip:int=0,db: Session = Depends(database.get_db)
                    ,current_user: models.User = Depends(oauth2.get_current_user)):

    orderitems = db.query(models.OrderItem).offset(skip).limit(limit).all()
    return orderitems
