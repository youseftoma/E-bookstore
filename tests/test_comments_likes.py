from fastapi import status  
from app.schemas import BookResponse

class TestCommentsLikesCreating:
    def test_create_comment(self, authorized_client_user1, test_book):
        book_id = test_book["id"]
        comment_content = "This is a new comment"
        response = authorized_client_user1.post("/book/comments", json={"book_id": book_id, "content": comment_content})
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["message"] == "Comment created successfully"
        get_response = authorized_client_user1.get(f"/books/{book_id}")
        assert get_response.status_code == status.HTTP_200_OK
        comments = get_response.json()["comments"]
        assert any(comment["content"] == comment_content for comment in comments)
    
    def test_create_like(self, authorized_client_user1, test_book):
        book_id = test_book["id"]
        response = authorized_client_user1.post("/book/likes", json={"object_id": book_id, "vote": "upvote"})
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["message"] == "Book liked successfully"
        book_response = authorized_client_user1.get(f"/books/{book_id}")
        assert book_response.status_code == status.HTTP_200_OK
        assert book_response.json()["likes"] == 1
    
    def test_create_like_on_comment(self, authorized_client_user1, test_comment):
        comment_id = test_comment["id"]
        response = authorized_client_user1.post("/comment/likes", json={"object_id": comment_id, "vote": "upvote"})
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["message"] == "Comment liked successfully"
        book_response = authorized_client_user1.get(f"/books/{test_comment['book_id']}")
        assert book_response.status_code == status.HTTP_200_OK
        comments = book_response.json()["comments"]
        for comment in comments:
            if comment["id"] == comment_id:
                assert comment["likes"] == 1
        

class TestGetLikesAndComments:

    def test_book_likes_and_comments(self, client, test_book, test_comment, test_like):
        book_id = test_book["id"]
        response = client.get(f"/books/{book_id}")
        assert response.status_code == status.HTTP_200_OK
        book = BookResponse(**response.json())
        assert isinstance(book.likes, int)
        assert isinstance(book.comments, list)
        assert len(book.comments) == 1
        assert book.comments[0].content == test_comment["content"]
        
    
class TestCommentsLikesUpdates:
    def test_update_comment(self, authorized_client_user1, test_comment):
        comment_id = test_comment["id"]
        new_content = "Updated comment content"
        response = authorized_client_user1.put(f"/book/comments/{comment_id}", json={"content": new_content})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Comment updated successfully"
        get_response = authorized_client_user1.get(f"/books/{test_comment['book_id']}")
        assert get_response.status_code == status.HTTP_200_OK
        comments = get_response.json()["comments"]
        assert any(comment["content"] == new_content for comment in comments)
    
class TestCommentsLikesDeleting:

    def test_delete_like(self, authorized_client_user2, test_book, test_like):
        book_id = test_book["id"]
        response = authorized_client_user2.post("/book/likes", json={"object_id": book_id, "vote": "remove"})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Like removed successfully"
        book_response = authorized_client_user2.get(f"/books/{book_id}")
        assert book_response.status_code == status.HTTP_200_OK
        assert book_response.json()["likes"] == 0

    def test_delete_like_on_comment(self, authorized_client_user2, test_comment, test_comment_like):
        comment_id = test_comment["id"]
        response = authorized_client_user2.post("/comment/likes", json={"object_id": comment_id, "vote": "remove"})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Like removed successfully"
        book_response = authorized_client_user2.get(f"/books/{test_comment['book_id']}")
        assert book_response.status_code == status.HTTP_200_OK
        comments = book_response.json()["comments"]
        for comment in comments:
            if comment["id"] == comment_id:
                assert comment["likes"] == 0

    def test_delete_comment(self, authorized_client_user2, test_comment):
        comment_id = test_comment["id"]
        response = authorized_client_user2.delete(f"/book/comments/{comment_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestCommentsLikesErrors:
    def test_like_nonexistent_book(self, authorized_client_user1):
        response = authorized_client_user1.post("/book/likes", json={"object_id": 9999, "vote": "upvote"})
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_like_nonexistent_comment(self, authorized_client_user1):
        response = authorized_client_user1.post("/comment/likes", json={"object_id": 9999, "vote": "upvote"})
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_nonexistent_comment(self, authorized_client_user1):
        response = authorized_client_user1.put("/comments/9999", json={"content": "New content"})
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_nonexistent_comment(self, authorized_client_user1):
        response = authorized_client_user1.delete("/comments/9999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_like_not_liked(self,test_admin_user, authorized_client_user1, test_book):
        book_id = test_book["id"]
        user_id = test_admin_user["id"]
        response = authorized_client_user1.post("/book/likes", json={"object_id": book_id, "vote": "remove"})
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
        assert response.json()["detail"] == f"the user of id {user_id} hadnt liked the book of id {book_id}"
    
    def test_delete_like_on_comment_not_liked(self,test_admin_user, authorized_client_user1, test_comment):
        comment_id = test_comment["id"]
        user_id = test_admin_user["id"]
        response = authorized_client_user1.post("/comment/likes", json={"object_id": comment_id, "vote": "remove"})
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
        assert response.json()["detail"] == f"the user of id {user_id} hadnt liked the comment of id {comment_id}"

