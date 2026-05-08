import pytest
from fastapi import status  
from app import models
from app.schemas import OrderResponse
from app.models import OrderStatus

class TestOrderEndpoints:

    class TestMyOrders:
        def test_get_my_orders(self, test_orders, authorized_client_user2):
            response = authorized_client_user2.get("/order/me")
            assert response.status_code == status.HTTP_200_OK
            order = [OrderResponse(**order) for order in response.json()]
            assert len(order) == 2
            assert order[0].name == test_orders[0]["name"]
        
        def test_get_my_orders_with_limit(self, test_orders, authorized_client_user2):
            response = authorized_client_user2.get("/order/me?limit=1")
            assert response.status_code == status.HTTP_200_OK
            order = [OrderResponse(**order) for order in response.json()]
            assert len(order) == 1
            assert order[0].name == test_orders[0]["name"]
            
        def test_get_my_orders_with_skip(self, test_orders, authorized_client_user2):
            response = authorized_client_user2.get("/order/me?skip=1")
            assert response.status_code == status.HTTP_200_OK
            order = [OrderResponse(**order) for order in response.json()]
            assert len(order) == 1
            assert order[0].name == test_orders[1]["name"]

        def test_get_my_orders_as_unverified_user(self, client):
            response = client.get("/order/me")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    

    class TestCreateOrders:
        def test_create_order(self,authorized_client_user2):
            new_order={"name": "new order"}
            response = authorized_client_user2.post("/order/",json=new_order)
        
            created_order = OrderResponse(**response.json())
            assert response.status_code == status.HTTP_201_CREATED
            assert created_order.name == new_order["name"]
        
        def test_create_order_as_unverified_user(self, client):
            new_order={"name": "new order"}
            response = client.post("/order/",json=new_order)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED


    class TestGetOrder_ByID:
        def test_get_order_by_id(self, test_orders, authorized_client_user2):
            response = authorized_client_user2.get(f"/order/{test_orders[1]['id']}")
            assert response.status_code == status.HTTP_200_OK
            order = OrderResponse(**response.json()) 
            assert order.name == test_orders[1]["name"]

        def test_get_order_not_yours(self, test_orders, authorized_client_user2):
            response = authorized_client_user2.get(f"/order/{test_orders[2]['id']}")
            assert response.status_code == status.HTTP_403_FORBIDDEN

        def test_get_order_by_id_not_found(self, authorized_client_user2):
            response = authorized_client_user2.get("/order/9999")
            assert response.status_code == status.HTTP_404_NOT_FOUND
        
        def test_get_order_by_id_invalid(self, authorized_client_user2):
            response = authorized_client_user2.get("/order/invalid")
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        def test_get_order_as_unverified_user(self, client):
            response = client.get("/order/1")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    class TestUpdateOrder:

        def test_update_order(self, test_orders, authorized_client_user2):
            new_order={"name": "update order"}
            response = authorized_client_user2.put(f"/order/{test_orders[1]['id']}",json=new_order)
            updated_order = OrderResponse(**response.json())
            assert response.status_code == status.HTTP_200_OK
            assert updated_order.name == new_order["name"]
        
        def test_update_order_not_yours(self, test_orders, authorized_client_user2):
            new_order={"name": "update order"}
            response = authorized_client_user2.put(f"/order/{test_orders[2]['id']}",json=new_order)
            assert response.status_code == status.HTTP_403_FORBIDDEN

        def test_update_order_by_id_not_found(self, authorized_client_user2):
            new_order={"name": "update order"}
            response = authorized_client_user2.put("/order/9999",json=new_order)
            assert response.status_code == status.HTTP_404_NOT_FOUND
        
        def test_update_order_by_id_invalid(self, authorized_client_user2):
            new_order={"name": "update order"}
            response = authorized_client_user2.put("/order/invalid",json=new_order)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        def test_update_order_as_unverified_user(self, client):
            new_order={"name": "update order"}
            response = client.put("/order/1",json=new_order)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED


    class TestDeleteOrder:

        def test_delete_order(self, test_orders, authorized_client_user2):
            response = authorized_client_user2.delete(f"/order/{test_orders[1]['id']}")
            assert response.status_code == status.HTTP_204_NO_CONTENT

        def test_delete_order_not_yours(self, test_orders, authorized_client_user2):
            response = authorized_client_user2.delete(f"/order/{test_orders[2]['id']}")
            assert response.status_code == status.HTTP_403_FORBIDDEN

        def test_delete_order_by_id_not_found(self, authorized_client_user2):
            response = authorized_client_user2.delete("/order/9999")
            assert response.status_code == status.HTTP_404_NOT_FOUND
        
        def test_delete_order_by_id_invalid(self, authorized_client_user2):
            response = authorized_client_user2.delete("/order/invalid")
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        def test_delete_order_as_unverified_user(self, client):
            response = client.delete("/order/1")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    class TestOrdering_The_Order:
        def test_ordering_the_order(self, test_orders, authorized_client_user2):
            payment_data = {"address": "123 Test St"}
            response = authorized_client_user2.put(f"/order/payment/{test_orders[1]['id']}",json=payment_data)
            updated_order = OrderResponse(**response.json())
            assert response.status_code == status.HTTP_200_OK
            assert updated_order.status == OrderStatus.ORDERED

        @pytest.mark.parametrize("invalid_status", ["ORDERED", "SHIPPED", "COMPLETED"])
        def test_ordering_already_processed_fails(
            self, session, test_orders, authorized_client_user2, invalid_status):

            order_id = test_orders[1]['id']
            db_order = session.query(models.Order).filter(models.Order.id == order_id).first()
            db_order.status = invalid_status
            session.commit()

            payment_data = {"address": "123 Test St"}
            response = authorized_client_user2.put(f"/order/payment/{order_id}", json=payment_data)

            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert response.json()["detail"] == f"this order is already {db_order.status}"

        def test_ordering_the_order_not_yours(self, test_orders, authorized_client_user2):
            payment_data = {"address": "123 Test St"}
            response = authorized_client_user2.put(f"/order/payment/{test_orders[2]['id']}",json=payment_data)
            assert response.status_code == status.HTTP_403_FORBIDDEN

        def test_ordering_the_order_by_id_not_found(self, authorized_client_user2):
            payment_data = {"address": "123 Test St"}
            response = authorized_client_user2.put("/order/payment/9999",json=payment_data)
            assert response.status_code == status.HTTP_404_NOT_FOUND

        def test_ordering_the_order_by_id_invalid(self, authorized_client_user2):
            payment_data = {"address": "123 Test St"}
            response = authorized_client_user2.put("/order/payment/invalid",json=payment_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        def test_ordering_the_order_as_unverified_user(self, client):
            payment_data = {"address": "123 Test St"}
            response = client.put("/order/payment/1",json=payment_data)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    
    class TestCancel_The_Order:
        def test_canceling_the_order(self,session, test_orders, authorized_client_user2):
            order_id = test_orders[1]['id']
            db_order = session.query(models.Order).filter(models.Order.id == order_id).first()
            db_order.status = OrderStatus.ORDERED
            session.commit()
            response = authorized_client_user2.put(f"/order/payment/cancel/{test_orders[1]['id']}")
            updated_order = OrderResponse(**response.json())
            assert response.status_code == status.HTTP_200_OK
            assert updated_order.status == OrderStatus.CANCELLED

        @pytest.mark.parametrize("invalid_status", ["CANCELLED", "PENDING", "COMPLETED"])
        def test_ordering_already_processed_fails(
            self, session, test_orders, authorized_client_user2, invalid_status):

            order_id = test_orders[1]['id']
            db_order = session.query(models.Order).filter(models.Order.id == order_id).first()
            db_order.status = invalid_status
            session.commit()
            response = authorized_client_user2.put(f"/order/payment/cancel/{order_id}")
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert response.json()["detail"] == f"this order is already {db_order.status}"

        def test_ordering_the_order_not_yours(self, test_orders, authorized_client_user2):
            payment_data = {"address": "123 Test St"}
            response = authorized_client_user2.put(f"/order/payment/cancel/{test_orders[2]['id']}",json=payment_data)
            assert response.status_code == status.HTTP_403_FORBIDDEN

        def test_ordering_the_order_by_id_not_found(self, authorized_client_user2):
            payment_data = {"address": "123 Test St"}
            response = authorized_client_user2.put("/order/payment/cancel/9999",json=payment_data)
            assert response.status_code == status.HTTP_404_NOT_FOUND

        def test_ordering_the_order_by_id_invalid(self, authorized_client_user2):
            payment_data = {"address": "123 Test St"}
            response = authorized_client_user2.put("/order/payment/cancel/invalid",json=payment_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        def test_ordering_the_order_as_unverified_user(self, client):
            payment_data = {"address": "123 Test St"}
            response = client.put("/order/payment/cancel/1",json=payment_data)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
class TestOrder_AdminEndpoints:

    class TestGetOrdered_Orders:

        def test_get_ordered_orders(self, session, test_orders, authorized_client_user1):
            # Set up orders with ORDERED status
            order_id = test_orders[0]['id']
            db_order = session.query(models.Order).filter(models.Order.id == order_id).first()
            db_order.status = models.OrderStatus.ORDERED
            session.commit()
            
            response = authorized_client_user1.get("/admins/order/ordered")
            assert response.status_code == status.HTTP_200_OK
            orders = [OrderResponse(**order) for order in response.json()]
            assert len(orders) >= 1
            assert any(order.id == order_id for order in orders)
        
        def test_get_ordered_orders_empty(self, authorized_client_user1):
            response = authorized_client_user1.get("/admins/order/ordered")
            assert response.status_code == status.HTTP_200_OK
            orders = response.json()
            assert isinstance(orders, list)
        
        def test_get_ordered_orders_as_unverified_user(self, client):
            response = client.get("/admins/order/ordered")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    class TestGetShipping_Orders:

        def test_get_shipping_orders(self, session, test_orders, authorized_client_user1):
            # Set up orders with SHIPPED status
            order_id = test_orders[0]['id']
            db_order = session.query(models.Order).filter(models.Order.id == order_id).first()
            db_order.status = models.OrderStatus.SHIPPED
            session.commit()
            
            response = authorized_client_user1.get("/admins/order/shiping")
            assert response.status_code == status.HTTP_200_OK
            orders = [OrderResponse(**order) for order in response.json()]
            assert any(order.id == order_id for order in orders)
        
        def test_get_shipping_orders_as_unverified_user(self, client):
            response = client.get("/admins/order/shiping")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    class TestGetCancelled_Orders:

        def test_get_cancelled_orders(self, session, test_orders, authorized_client_user1):
            # Set up orders with CANCELLED status
            order_id = test_orders[0]['id']
            db_order = session.query(models.Order).filter(models.Order.id == order_id).first()
            db_order.status = models.OrderStatus.CANCELLED
            session.commit()
            
            response = authorized_client_user1.get("/admins/order/cancel")
            assert response.status_code == status.HTTP_200_OK
            orders = [OrderResponse(**order) for order in response.json()]
            assert any(order.id == order_id for order in orders)
        
        def test_get_cancelled_orders_as_unverified_user(self, client):
            response = client.get("/admins/order/cancel")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    class TestGetCompleted_Orders:

        def test_get_completed_orders(self, test_orders, authorized_client_user1):
            # test_orders[2] is already COMPLETED
            response = authorized_client_user1.get("/admins/order/completing")
            assert response.status_code == status.HTTP_200_OK
            orders = [OrderResponse(**order) for order in response.json()]
            assert len(orders) >= 1
            assert any(order.id == test_orders[2]['id'] for order in orders)
        
        def test_get_completed_orders_as_unverified_user(self, client):
            response = client.get("/admins/order/completing")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    class TestMakeOrderShipping:

        def test_make_order_shipping(self, session, test_orders, authorized_client_user1):
            order_id = test_orders[0]['id']
            db_order = session.query(models.Order).filter(models.Order.id == order_id).first()
            db_order.status = models.OrderStatus.ORDERED
            session.commit()
            
            response = authorized_client_user1.put(f"/admins/order/shiping/{order_id}")
            updated_order = OrderResponse(**response.json())
            assert response.status_code == status.HTTP_200_OK
            assert updated_order.status == models.OrderStatus.SHIPPED
        
        @pytest.mark.parametrize("invalid_status", ["CANCELLED", "PENDING", "SHIPPED", "COMPLETED"])
        def test_make_order_shipping_fails_for_invalid_status(
            self, session, test_orders, authorized_client_user1, invalid_status):
            order_id = test_orders[0]['id']
            db_order = session.query(models.Order).filter(models.Order.id == order_id).first()
            db_order.status = invalid_status
            session.commit()
            
            response = authorized_client_user1.put(f"/admins/order/shiping/{order_id}")
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert response.json()["detail"] == f"this order is already {db_order.status}"
        
        def test_make_order_shipping_not_found(self, authorized_client_user1):
            response = authorized_client_user1.put("/admins/order/shiping/9999")
            assert response.status_code == status.HTTP_404_NOT_FOUND
        
        def test_make_order_shipping_invalid_id(self, authorized_client_user1):
            response = authorized_client_user1.put("/admins/order/shiping/invalid")
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        
        def test_make_order_shipping_as_unverified_user(self, client):
            response = client.put("/admins/order/shiping/1")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    class TestMakeOrderCompleted:

        def test_make_order_completed(self, session, test_orders, authorized_client_user1):
            order_id = test_orders[0]['id']
            db_order = session.query(models.Order).filter(models.Order.id == order_id).first()
            db_order.status = models.OrderStatus.SHIPPED
            session.commit()
            
            response = authorized_client_user1.put(f"/admins/order/completing/{order_id}")
            updated_order = OrderResponse(**response.json())
            assert response.status_code == status.HTTP_200_OK
            assert updated_order.status == models.OrderStatus.COMPLETED
        
        @pytest.mark.parametrize("invalid_status", ["CANCELLED", "PENDING", "ORDERED", "COMPLETED"])
        def test_make_order_completed_fails_for_invalid_status(
            self, session, test_orders, authorized_client_user1, invalid_status):
            order_id = test_orders[0]['id']
            db_order = session.query(models.Order).filter(models.Order.id == order_id).first()
            db_order.status = invalid_status
            session.commit()
            
            response = authorized_client_user1.put(f"/admins/order/completing/{order_id}")
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert response.json()["detail"] == f"this order is already {db_order.status}"
        
        def test_make_order_completed_not_found(self, authorized_client_user1):
            response = authorized_client_user1.put("/admins/order/completing/9999")
            assert response.status_code == status.HTTP_404_NOT_FOUND
        
        def test_make_order_completed_invalid_id(self, authorized_client_user1):
            response = authorized_client_user1.put("/admins/order/completing/invalid")
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        
        def test_make_order_completed_as_unverified_user(self, client):
            response = client.put("/admins/order/completing/1")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED