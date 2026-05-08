from fastapi import status
from app.schemas import OrderItemResponse


class TestOrderItemEndpoints:

    class TestCreateOrderItem:

        def test_create_orderitem(self, authorized_client_user2, test_orders, test_book, session):
            create_data = {
                "order_id": test_orders[0]["id"],
                "book_id": test_book["id"],
                "quantity": 3
            }
            response = authorized_client_user2.post("/orderitems/", json=create_data)
            assert response.status_code == status.HTTP_201_CREATED
            order_item = OrderItemResponse(**response.json())
            assert order_item.order_id == create_data["order_id"]
            assert order_item.book_id == create_data["book_id"]
            assert order_item.quantity == create_data["quantity"]
        
        def test_create_orderitem_invalid_book(self, authorized_client_user2, test_orders):
            create_data = {
                "order_id": test_orders[0]["id"],
                "book_id": 9999,
                "quantity": 3
            }
            response = authorized_client_user2.post("/orderitems/", json=create_data)
            assert response.status_code == status.HTTP_404_NOT_FOUND
        
        def test_create_orderitem_invalid_order(self, authorized_client_user2, test_book):
            create_data = {
                "order_id": 9999,
                "book_id": test_book["id"],
                "quantity": 3
            }
            response = authorized_client_user2.post("/orderitems/", json=create_data)
            assert response.status_code == status.HTTP_404_NOT_FOUND
        
        def test_create_orderitem_as_unverified_user(self, client, test_orders, test_book):
            create_data = {
                "order_id": test_orders[0]["id"],
                "book_id": test_book["id"],
                "quantity": 3
            }
            response = client.post("/orderitems/", json=create_data)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    class TestGetOrderItem:

        def test_get_orderitem(self, authorized_client_user2, test_order_item):
            response = authorized_client_user2.get(f"/orderitems/{test_order_item['id']}")
            assert response.status_code == status.HTTP_200_OK
            order_item = OrderItemResponse(**response.json())
            assert order_item.id == test_order_item["id"]
            assert order_item.quantity == test_order_item["quantity"]
        
        def test_get_orderitem_not_yours(self, authorized_client_user2, test_order_items):
            response = authorized_client_user2.get(f"/orderitems/{test_order_items[2]['id']}")
            assert response.status_code == status.HTTP_403_FORBIDDEN
        
        def test_get_orderitem_not_found(self, authorized_client_user2):
            response = authorized_client_user2.get("/orderitems/9999")
            assert response.status_code == status.HTTP_404_NOT_FOUND
        
        def test_get_orderitem_invalid_id(self, authorized_client_user2):
            response = authorized_client_user2.get("/orderitems/invalid")
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        
        def test_get_orderitem_as_unverified_user(self, client):
            response = client.get("/orderitems/1")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    class TestUpdateOrderItem:

        def test_update_orderitem(self, authorized_client_user2, test_order_items, session):
            order_item_id = test_order_items[0]["id"]
            update_data = {"quantity": 5}
            response = authorized_client_user2.put(f"/orderitems/{order_item_id}", json=update_data)
            assert response.status_code == status.HTTP_200_OK
            updated_item = OrderItemResponse(**response.json())
            assert updated_item.quantity == update_data["quantity"]
        
        def test_update_orderitem_not_yours(self, authorized_client_user2, test_order_items):
            update_data = {"quantity": 5}
            response = authorized_client_user2.put(f"/orderitems/{test_order_items[2]['id']}", json=update_data)
            assert response.status_code == status.HTTP_403_FORBIDDEN
        
        def test_update_orderitem_not_found(self, authorized_client_user2):
            update_data = {"quantity": 5}
            response = authorized_client_user2.put("/orderitems/9999", json=update_data)
            assert response.status_code == status.HTTP_404_NOT_FOUND
        
        def test_update_orderitem_invalid_id(self, authorized_client_user2):
            update_data = {"quantity": 5}
            response = authorized_client_user2.put("/orderitems/invalid", json=update_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        
        def test_update_orderitem_as_unverified_user(self, client):
            update_data = {"quantity": 5}
            response = client.put("/orderitems/1", json=update_data)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    class TestDeleteOrderItem:

        def test_delete_orderitem(self, authorized_client_user2, test_order_items):
            order_item_id = test_order_items[0]["id"]
            response = authorized_client_user2.delete(f"/orderitems/{order_item_id}")
            assert response.status_code == status.HTTP_204_NO_CONTENT
        
        def test_delete_orderitem_not_yours(self, authorized_client_user2, test_order_items):
            response = authorized_client_user2.delete(f"/orderitems/{test_order_items[2]['id']}")
            assert response.status_code == status.HTTP_403_FORBIDDEN
        
        def test_delete_orderitem_not_found(self, authorized_client_user2):
            response = authorized_client_user2.delete("/orderitems/9999")
            assert response.status_code == status.HTTP_404_NOT_FOUND
        
        def test_delete_orderitem_invalid_id(self, authorized_client_user2):
            response = authorized_client_user2.delete("/orderitems/invalid")
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        
        def test_delete_orderitem_as_unverified_user(self, client):
            response = client.delete("/orderitems/1")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestOrderItem_AdminEndpoints:

    class TestGetAllOrderItems:

        def test_get_all_orderitems(self, authorized_client_user1, test_order_items):
            response = authorized_client_user1.get("/admins/orderitems/")
            assert response.status_code == status.HTTP_200_OK
            items = [OrderItemResponse(**item) for item in response.json()]
            assert len(items) >= len(test_order_items)
        
        def test_get_all_orderitems_with_limit(self, authorized_client_user1, test_order_items):
            response = authorized_client_user1.get("/admins/orderitems/?limit=1")
            assert response.status_code == status.HTTP_200_OK
            items = response.json()
            assert len(items) <= 1
        
        def test_get_all_orderitems_with_skip(self, authorized_client_user1, test_order_items):
            response = authorized_client_user1.get("/admins/orderitems/?skip=1")
            assert response.status_code == status.HTTP_200_OK
            items = response.json()
            assert isinstance(items, list)
        
        def test_get_all_orderitems_as_unverified_user(self, client):
            response = client.get("/admins/orderitems/")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED