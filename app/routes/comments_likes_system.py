from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from sqlalchemy.orm import Session
from ..  import models,schemas,database,oauth2,utils
from ..limiter import limiter

route = APIRouter(tags=["comments_and_likes"])

@route.post("/book/likes",status_code=status.HTTP_201_CREATED)
@limiter.limit("15/minute")
def liking_book(request: Request,response: Response,createlike: schemas.CreateLIke ,db: Session = Depends(database.get_db),
                 current_user: models.User = Depends(oauth2.get_current_user)):
    
    utils.get_book_or_404(createlike.object_id,db)
    query_like= db.query(models.Book_Like).filter(models.Book_Like.book_id == createlike.object_id
                                                  ,models.Book_Like.user_id ==current_user.id)
    like = query_like.first()
    if createlike.vote == "upvote":
        if like:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    detail=f"the user of id {current_user.id} already liked the book of id {createlike.object_id}")
        createdlike = models.Book_Like(user_id = current_user.id ,book_id = createlike.object_id)
        db.add(createdlike)
        db.commit()
        db.refresh(createdlike)
        return {"message": "Book liked successfully"}
    else: 
        if not like:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    detail=f"the user of id {current_user.id} hadnt liked the book of id {createlike.object_id}")
        db.delete(like)
        db.commit()
        response.status_code = status.HTTP_200_OK 
        return {"message": "Like removed successfully"}
    

@route.post("/comment/likes",status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def liking_comment(request: Request,response: Response,createlike: schemas.CreateLIke ,db: Session = Depends(database.get_db),
                 current_user: models.User = Depends(oauth2.get_current_user)):
    
    utils.get_comment_or_404(createlike.object_id,db)
    query_like= db.query(models.Comment_Like).filter(models.Comment_Like.comment_id == createlike.object_id
                                                  ,models.Comment_Like.user_id ==current_user.id)
    like = query_like.first()
    if createlike.vote == "upvote":
        if like:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    detail=f"the user of id {current_user.id} already liked the comment of id {createlike.object_id}")
        createdlike = models.Comment_Like(user_id = current_user.id ,comment_id = createlike.object_id)
        db.add(createdlike)
        db.commit()
        db.refresh(createdlike)
        return {"message": "Comment liked successfully"}
    else: 
        if not like:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    detail=f"the user of id {current_user.id} hadnt liked the comment of id {createlike.object_id}")
        db.delete(like)
        db.commit()
        response.status_code = status.HTTP_200_OK 
        return {"message": "Like removed successfully"}
    


@route.post("/book/comments",status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def create_comment(request: Request,create_comment: schemas.CreateComment,db: Session = Depends(database.get_db)
                    ,current_user: models.User = Depends(oauth2.get_current_user)):
    
    utils.get_book_or_404(create_comment.book_id,db)
    comment = models.Comment(user_id= current_user.id,
                         book_id= create_comment.book_id,
                         content= create_comment.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return {"message": "Comment created successfully"}


@route.put("/book/comments/{id}")
@limiter.limit("10/minute")
def update_comment(request: Request,id:int ,update_comment: schemas.UpdateComment, db: Session = Depends(database.get_db)
                    ,current_user: models.User = Depends(oauth2.get_current_user)):

    comment = utils.get_comment_or_404(id,db).first()
    utils.verify_owner_or_403(comment.user_id,db,current_user)
    comment.content = update_comment.content
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return {"message": "Comment updated successfully"}    


@route.delete("/book/comments/{id}",status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
def delete_comment(request: Request,id:int ,db: Session = Depends(database.get_db)
                    ,current_user: models.User = Depends(oauth2.get_current_user)):
    
    comment = utils.get_comment_or_404(id,db).first()
    utils.verify_owner_or_403(comment.user_id,db,current_user)
    db.delete(comment)
    db.commit()   