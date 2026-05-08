from fastapi import status  
from app.schemas import BookResponse, BookCreateResponse

class TestBookEndpoints:

    class TestGetBooks:
        def test_get_books(self, client, test_books):
            response = client.get("/books/")
            assert response.status_code == status.HTTP_200_OK
            books = [BookResponse(**book) for book in response.json()]
            assert len(books) == len(test_books)

        def test_get_books_with_search(self, client, test_books):
            search_term = "Book One"
            response = client.get(f"/books/?search={search_term}")
            assert response.status_code == status.HTTP_200_OK
            books = [BookResponse(**book) for book in response.json()]
            assert len(books) == 1
            assert books[0].name == search_term

        def test_get_books_with_category_filter(self, client, test_books):
            category = "Fiction"
            response = client.get(f"/books/?category={category}")
            assert response.status_code == status.HTTP_200_OK
            books = [BookResponse(**book) for book in response.json()]
            assert all(category in book.categories for book in books)
        
        def test_get_books_with_pagination(self, client, test_books):
            response = client.get("/books/?limit=2&skip=1")
            assert response.status_code == status.HTTP_200_OK
            books = [BookResponse(**book) for book in response.json()]
            assert len(books) == 2
            assert books[0].id == test_books[1]["id"]

    
    class TestGetBookById:
        def test_get_book_by_id(self, client, test_books):
            book_id = test_books[0]["id"]
            response = client.get(f"/books/{book_id}")
            assert response.status_code == status.HTTP_200_OK
            book = BookResponse(**response.json())
            assert book.id == book_id
        
        def test_get_book_by_id_not_found(self, client):
            response = client.get("/books/9999")
            assert response.status_code == status.HTTP_404_NOT_FOUND
        
        def test_get_book_by_id_invalid(self, client):
            response = client.get("/books/invalid")
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        
    
class TestBook_AdminEndpoints:

    class TestCreateBook:
        def test_create_book_as_admin(self, authorized_client_user1):
            new_book = {
                "name": "New Book",
                "author": "New Author",
                "description": "A new book description",
                "categories": ["Fiction"],
                "price": 19.99,
                "stock": 50
            }
            response = authorized_client_user1.post("/admins/books/", json=new_book)
            assert response.status_code == status.HTTP_201_CREATED
            created_book = BookCreateResponse(**response.json())
            assert created_book.name == new_book["name"]
            assert created_book.author == new_book["author"]
        
        def test_create_book_as_non_admin(self, authorized_client_user2):
            new_book = {
                "name": "New Book",
                "author": "New Author",
                "description": "A new book description",
                "categories": ["Fiction"],
                "price": 19.99,
                "stock": 50
            }
            response = authorized_client_user2.post("/admins/books/", json=new_book)
            assert response.status_code == status.HTTP_403_FORBIDDEN
        
        def test_create_book_with_invalid_data(self, authorized_client_user1):
            new_book = {
                "name": "",
                "author": "New Author",
                "description": "A new book description",
                "categories": ["Fiction"],
                "price": -10.00,
                "stock": -5
            }
            response = authorized_client_user1.post("/admins/books/", json=new_book)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        
        def test_create_book_with_missing_fields(self, authorized_client_user1):
            new_book = {
                "name": "New Book",
                "author": "New Author",
                "description": "A new book description",
                "categories": ["Fiction"],
                "price": 19.99
            }
            response = authorized_client_user1.post("/admins/books/", json=new_book)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        
    
    class TestUpdateBook:

        # update book tests is similar to create book tests, only added the book id test cases
        def test_update_book(self, authorized_client_user1, test_book):
            book_id = test_book["id"]
            updated_data = {
                "name": "Updated Book",
                "author": "Updated Author",
                "description": "An updated book description",
                "categories": ["Non-Fiction"],
                "price": 29.99,
                "stock": 30
            }
            response = authorized_client_user1.put(f"/admins/books/{book_id}", json=updated_data)
            assert response.status_code == status.HTTP_200_OK
            updated_book = BookCreateResponse(**response.json())
            assert updated_book.name == updated_data["name"]
            assert updated_book.author == updated_data["author"]
        
        def test_update_book_not_found(self, authorized_client_user1):
            updated_data = {
                "name": "Updated Book",
                "author": "Updated Author",
                "description": "An updated book description",
                "categories": ["Non-Fiction"],
                "price": 29.99,
                "stock": 30
            }
            response = authorized_client_user1.put("/admins/books/9999", json=updated_data)
            assert response.status_code == status.HTTP_404_NOT_FOUND

    class TestDeleteBook:

        def test_delete_book(self, authorized_client_user1, test_book):
            book_id = test_book["id"]
            response = authorized_client_user1.delete(f"/admins/books/{book_id}")
            assert response.status_code == status.HTTP_204_NO_CONTENT

        def test_delete_book_not_found(self, authorized_client_user1):
            response = authorized_client_user1.delete("/admins/books/9999")
            assert response.status_code == status.HTTP_404_NOT_FOUND
        
        def test_delete_book_as_non_admin(self, authorized_client_user2, test_book):
            book_id = test_book["id"]
            response = authorized_client_user2.delete(f"/admins/books/{book_id}")
            assert response.status_code == status.HTTP_403_FORBIDDEN

