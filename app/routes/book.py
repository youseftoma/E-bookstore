from fastapi import APIRouter, status,Depends, Request
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal
from ..  import models,schemas,database,oauth2,utils
from ..limiter import limiter

route = APIRouter(
    prefix= "/books",
    tags=["books"]
          )

# Admin router
adminroute = APIRouter(
    prefix="/admins/books",
    tags=["books", "admins"],
    dependencies=[Depends(utils.admin_only)])


# get books

@route.get("/", response_model=list[schemas.BookResponse])
@limiter.limit("2/5 seconds; 15/minute")
def get_books(request: Request,limit: int = 10, skip: int = 0, search: Optional[str] = None,category: Optional[str] = None,
               price: Decimal  = 00.0, db: Session = Depends(database.get_db)):

    query = (db.query(models.Book, func.count(models.Book_Like.book_id).label("likes"))
             .join(models.Book_Like, models.Book_Like.book_id == models.Book.id, isouter=True)
             .group_by(models.Book.id))
    
    if search:
        query = query.filter(models.Book.name.contains(search))

    if category:
        query = query.filter(models.Book.categories.contains([category]))   
    
    results = query.filter(models.Book.price >= price).offset(skip).limit(limit).all()

    final_results = []
    for book, likes in results:
        # Attach the 'likes' count to the book object dynamically
        book.likes = likes
        final_results.append(book)

    return final_results

# get by id

@route.get("/{id}", response_model=schemas.BookResponse)
@limiter.limit("10/minute")
def get_book(request: Request, id: int, db: Session = Depends(database.get_db)):
    utils.get_book_or_404(id,db)
    result = (db.query(models.Book, func.count(models.Book_Like.book_id).label("likes"))
              .join(models.Book_Like, models.Book_Like.book_id == models.Book.id, isouter=True)
              .filter(models.Book.id == id)
              .group_by(models.Book.id)
              .first())
    book, book_likes = result
    book.likes = book_likes

    return book

# create book

@adminroute.post("/",response_model=schemas.BookCreateResponse,status_code= status.HTTP_201_CREATED)
def create_book(create_book: schemas.CreateBook ,db: Session = Depends(database.get_db)
                ,current_user: models.User = Depends(oauth2.get_current_user)):
    book = models.Book(**create_book.dict())
    db.add(book)
    db.commit()
    db.refresh(book)
    return book

#update book

@adminroute.put("/{id}",response_model=schemas.BookCreateResponse)
def update_book(id:int ,update_book: schemas.CreateBook ,db: Session = Depends(database.get_db),current_user: models.User = Depends(oauth2.get_current_user)):
    
    book = utils.get_book_or_404(id,db)
    # Update fields
    book.update(update_book.dict(), synchronize_session=False)
    db.commit()
    return book.first()

#delete book

@adminroute.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_book(id:int ,db: Session = Depends(database.get_db),current_user: models.User = Depends(oauth2.get_current_user)):

    book = utils.get_book_or_404(id,db).first()
    db.delete(book)
    db.commit()

