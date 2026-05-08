from fastapi import status  
from app.schemas import UserResponse, UserAdminResponse ,BanUserResponse

class Test_UserEndpoints:

    class TestUser_Create:
        def test_create_user(self, client):
            user_data = {
                "email": "test@example.com",
                "role": "user",
                "phone": "01011758453",
                "region": "EG",
                "hashed_password": "password123"
            }
            response = client.post("/users/", json=user_data)
            new_user = UserResponse(**response.json())
            assert response.status_code == status.HTTP_201_CREATED
        
        def test_create_user_with_existing_email(self, client, test_unverified_user):
            user_data = {
                "email": test_unverified_user["email"],
                "role": "user",
                "phone": "01011758454",
                "region": "EG",
                "hashed_password": "password123"
            }
            response = client.post("/users/", json=user_data)
            assert response.status_code == status.HTTP_400_BAD_REQUEST

        def test_create_user_with_invalid_phone(self, client):
            user_data = {
                "email": "test@example.com",
                "role": "user",
                "phone": "1234",  # Invalid phone number
                "region": "EG",
                "hashed_password": "password123"
            }
            response = client.post("/users/", json=user_data)
            assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
        
        def test_create_user_with_invalid_email(self, client):
            user_data = {
                "email": "invalid-email",  # Invalid email format
                "role": "user",
                "phone": "01011758453",
                "region": "EG",
                "hashed_password": "password123"
            }
            response = client.post("/users/", json=user_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        
        def test_create_user_with_missing_fields(self, client):
            user_data = {
                "email": "test@example.com",
                "role": "user",
                "phone": "01011758453",
                "region": "EG",
                "hashed_password": "password123"
            }
            # Remove a required field to test the validation-
            del user_data["email"]
            response = client.post("/users/", json=user_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        def test_create_user_with_banned_email(self, client, test_banned_user):
            user_data = {
                "email": test_banned_user["user"]["email"],
                "role": "user",
                "phone": "01011758453",
                "region": "EG",
                "hashed_password": "password123"
            }
            response = client.post("/users/", json=user_data)
            assert response.status_code == status.HTTP_403_FORBIDDEN
        
        def test_create_user_with_expired_ban_email(self, client, test_banned_user_expired):
            user_data = {
                "email": test_banned_user_expired["user"]["email"],
                "role": "user",
                "phone": "01011758453",
                "region": "EG",
                "hashed_password": "password123"
            }
            response = client.post("/users/", json=user_data)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
        

    class TestUser_VerifyGmail:
        def test_verify_gmail(self, client, test_unverified_user):
            response = client.get(f"/users/verify_gmail/{test_unverified_user['token']}")
            assert response.status_code == status.HTTP_200_OK
            assert response.json() == {"message": "Verification email successfully"}
        
        def test_verify_gmail_with_invalid_token(self, client):
            response = client.get("/users/verify_gmail/invalidtoken")
            assert response.status_code == status.HTTP_404_NOT_FOUND
        
        def test_verify_gmail_already_verified(self, client, test_verify_user):
            # First verify the user's email
            client.get(f"/users/verify_gmail/{test_verify_user['token']}")
            # Attempt to verify again
            response = client.get(f"/users/verify_gmail/{test_verify_user['token']}")
            assert response.status_code == status.HTTP_403_FORBIDDEN

        def test_verify_gmail_with_banned_email(self, client, test_banned_user):
            response = client.get(f"/users/verify_gmail/{test_banned_user['user']['token']}")
            assert response.status_code == status.HTTP_403_FORBIDDEN
            

    class TestUser_ResetPassword:
        def test_reset_password(self, client, test_verify_user):
            reset_data = {
                "email": test_verify_user["email"],
                "phone": test_verify_user["phone_number"],
                "region": test_verify_user["region"],
                "new_password": "newpassword123"
            }
            response = client.put("/users/reset_password", json=reset_data)
            assert response.status_code == status.HTTP_200_OK
        
        def test_reset_password_with_invalid_credentials(self, client):
            reset_data = {
                "email": "invalid@example.com",
                "phone": "01011758453",
                "region": "EG",
                "new_password": "newpassword123"
            }
            response = client.put("/users/reset_password", json=reset_data)
            assert response.status_code == status.HTTP_403_FORBIDDEN
        
        def test_reset_password_with_invalid_phone(self, client, test_verify_user):
            reset_data = {
                "email": test_verify_user["email"],
                "phone": "invalidphone",
                "region": test_verify_user["region"],
                "new_password": "newpassword123"
            }
            response = client.put("/users/reset_password", json=reset_data)
            assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
        
        def test_reset_password_with_banned_email(self, client, test_banned_user):
            reset_data = {
                "email": test_banned_user["user"]["email"],
                "phone": test_banned_user["user"]["phone_number"],
                "region": test_banned_user["user"]["region"],
                "new_password": "newpassword123"
            }
            response = client.put("/users/reset_password", json=reset_data)
            assert response.status_code == status.HTTP_403_FORBIDDEN
        
        def test_reset_password_with_expired_ban_email(self, client, test_banned_user_expired):
            reset_data = {
                "email": test_banned_user_expired["user"]["email"],
                "phone": test_banned_user_expired["user"]["phone_number"],
                "region": test_banned_user_expired["user"]["region"],
                "new_password": "newpassword123"
            }
            response = client.put("/users/reset_password", json=reset_data)
            assert response.status_code == status.HTTP_200_OK


    class TestUser_ChangePassword:
        def test_change_password(self, authorized_client_user2, test_verify_user):
            change_data = {
                "password": test_verify_user["hashed_password"],
                "new_password": "newpassword123"
            }
            response = authorized_client_user2.put("/users/change_password", json=change_data)
            assert response.status_code == status.HTTP_200_OK
        
        def test_change_password_with_invalid_current_password(self, authorized_client_user2):
            change_data = {
                "password": "invalidpassword",
                "new_password": "newpassword123"
            }
            response = authorized_client_user2.put("/users/change_password", json=change_data)
            assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE


    class TestUser_GetProfile:
        def test_get_user_profile(self, authorized_client_user2, test_verify_user):
            response = authorized_client_user2.get("/users/me")
            assert response.status_code == status.HTTP_200_OK
            user_profile = UserResponse(**response.json())
            assert user_profile.email == test_verify_user["email"]

class TestUser_AdminEndpoints:
    
    class TestUser_GetAllUsers:
        def test_get_all_users_as_admin(self, test_users,authorized_client_user1):
            response = authorized_client_user1.get("/admins/users/")
            assert response.status_code == status.HTTP_200_OK
            users = [UserAdminResponse(**user) for user in response.json()]
            assert len(response.json()) == len(test_users)+1  # +1 for the admin user

        def test_get_all_users_as_non_admin(self, authorized_client_user2):
            response = authorized_client_user2.get("/admins/users/")
            assert response.status_code == status.HTTP_403_FORBIDDEN
        
        def test_get_all_users_with_role_filter(self, test_users, authorized_client_user1):
            response = authorized_client_user1.get("/admins/users/?role=user")
            assert response.status_code == status.HTTP_200_OK
            users = [UserAdminResponse(**user) for user in response.json()]
            for user in users:
                assert user.role == "user"
            assert len(response.json()) == 2 # Only the 2 regular users, not the admin
        
        def test_get_all_users_with_pagination(self, test_users, authorized_client_user1):
            response = authorized_client_user1.get("/admins/users/?limit=2&skip=1")
            assert response.status_code == status.HTTP_200_OK
            users = [UserAdminResponse(**user) for user in response.json()]
            assert len(users) == 2
            assert users[0].email == test_users[1]["email"]   # Skip the first user and get the next 2

    class TestUser_GetUserById:
        def test_get_user_by_id_as_admin(self, test_verify_user, authorized_client_user1):
            response = authorized_client_user1.get(f"/admins/users/{test_verify_user['id']}")
            assert response.status_code == status.HTTP_200_OK
            user_data = UserAdminResponse(**response.json())
            assert user_data.email == test_verify_user["email"]
        
        def test_get_user_by_id_as_non_admin(self, test_verify_user, authorized_client_user2):
            response = authorized_client_user2.get(f"/admins/users/{test_verify_user['id']}")
            assert response.status_code == status.HTTP_403_FORBIDDEN
        
        def test_get_user_by_id_not_found(self, authorized_client_user1):
            response = authorized_client_user1.get("/admins/users/9999")  # Assuming this ID does not exist
            assert response.status_code == status.HTTP_404_NOT_FOUND
        
    class TestUser_DeleteUser:
        def test_delete_user_as_admin(self, test_verify_user, authorized_client_user1):
            response = authorized_client_user1.delete(f"/admins/users/{test_verify_user['id']}")
            assert response.status_code == status.HTTP_204_NO_CONTENT
        
        def test_delete_user_as_non_admin(self, test_verify_user, authorized_client_user2):
            response = authorized_client_user2.delete(f"/admins/users/{test_verify_user['id']}")
            assert response.status_code == status.HTTP_403_FORBIDDEN
        
        def test_delete_user_not_found(self, authorized_client_user1):
            response = authorized_client_user1.delete("/admins/users/9999")  # Assuming this ID does not exist
            assert response.status_code == status.HTTP_404_NOT_FOUND
        
        def test_delete_self(self, test_admin_user,authorized_client_user1):
            response = authorized_client_user1.delete(f"/admins/users/{test_admin_user['id']}")
            assert response.status_code == status.HTTP_403_FORBIDDEN
        
    class TestUser_GetBannedUsers:
        def test_get_banned_users_as_admin(self, test_banned_users, authorized_client_user1):
            response = authorized_client_user1.get("/admins/ban/users/")
            assert response.status_code == status.HTTP_200_OK
            banned_users = [BanUserResponse(**user) for user in response.json()]
            assert len(banned_users) == len(test_banned_users)

        def test_get_banned_users_as_non_admin(self,authorized_client_user2):
            response = authorized_client_user2.get("/admins/ban/users")
            assert response.status_code == status.HTTP_403_FORBIDDEN

        def test_get_banned_users_with_role_filter(self, test_banned_user, authorized_client_user1):
            response = authorized_client_user1.get("/admins/ban/users/?role=user")
            assert response.status_code == status.HTTP_200_OK
            banned_users = [BanUserResponse(**user) for user in response.json()]
            assert len(banned_users) == 1

        def test_get_banned_users_with_pagination(self, test_banned_users, authorized_client_user1):
            response = authorized_client_user1.get("/admins/ban/users/?limit=2&skip=1")
            assert response.status_code == status.HTTP_200_OK
            banned_users = [BanUserResponse(**user) for user in response.json()]
            assert len(banned_users) == 2
            assert banned_users[0].email == test_banned_users[1]["email"]  # Skip the first banned user and get the next 2
        
    class TestUser_BanUserCreate:
        def test_ban_user_as_admin(self, test_verify_user, authorized_client_user1):
            ban_data = {
                "user_id": test_verify_user["id"],
                "years": 1,
                "months": 0
            }
            response = authorized_client_user1.post("/admins/ban/users/", json=ban_data)
            assert response.status_code == status.HTTP_201_CREATED
            banned_user = BanUserResponse(**response.json())
            assert banned_user.email == test_verify_user["email"]
        
        def test_ban_user_as_non_admin(self, test_verify_user, authorized_client_user2):
            ban_data = {
                "user_id": test_verify_user["id"],
                "years": 1,
                "months": 0
            }
            response = authorized_client_user2.post("/admins/ban/users/", json=ban_data)
            assert response.status_code == status.HTTP_403_FORBIDDEN
        
        def test_ban_nonexistent_user(self, authorized_client_user1):
            ban_data = {
                "user_id": 9999,  # Assuming this ID does not exist
                "years": 1,
                "months": 0
            }
            response = authorized_client_user1.post("/admins/ban/users/", json=ban_data)
            assert response.status_code == status.HTTP_404_NOT_FOUND
        
        def test_ban_self(self, test_admin_user, authorized_client_user1):
            ban_data = {
                "user_id": test_admin_user["id"],
                "years": 1,
                "months": 0
            }
            response = authorized_client_user1.post("/admins/ban/users/", json=ban_data)
            assert response.status_code == status.HTTP_403_FORBIDDEN

        def test_ban_user_with_existing_ban(self, test_banned_user, authorized_client_user1):
            ban_data = {
                "user_id": test_banned_user["user"]["id"],
                "years": 1,
                "months": 0
            }
            response = authorized_client_user1.post("/admins/ban/users/", json=ban_data)
            assert response.status_code == status.HTTP_403_FORBIDDEN
        
        def test_ban_user_with_expired_ban(self, test_banned_user_expired, authorized_client_user1):
            ban_data = {
                "user_id": test_banned_user_expired["user"]["id"],
                "years": 1,
                "months": 0
            }
            response = authorized_client_user1.post("/admins/ban/users/", json=ban_data)
            assert response.status_code == status.HTTP_201_CREATED
            banned_user = BanUserResponse(**response.json())
        
        def test_ban_user_with_invalid_ban_date(self, test_verify_user, authorized_client_user1):
            ban_data = {
                "user_id": test_verify_user["id"],
                "years": -1,
                "months": 0
            }
            response = authorized_client_user1.post("/admins/ban/users/", json=ban_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    class TestUser_BanUserUpdate:
        def test_update_ban_user_as_admin(self, test_banned_user, authorized_client_user1):
            update_data = {
                "years": 2,
                "months": 0
            }
            response = authorized_client_user1.put(f"/admins/ban/users/{test_banned_user['ban']['id']}", json=update_data)
            assert response.status_code == status.HTTP_200_OK
            updated_ban = BanUserResponse(**response.json())
            assert updated_ban.email == test_banned_user["user"]["email"]
        
        def test_update_ban_user_as_non_admin(self, test_banned_user, authorized_client_user2):
            update_data = {
                "years": 2,
                "months": 0
            }
            response = authorized_client_user2.put(f"/admins/ban/users/{test_banned_user['ban']['id']}", json=update_data)
            assert response.status_code == status.HTTP_403_FORBIDDEN
        
        def test_update_nonexistent_ban_user(self, authorized_client_user1):
            update_data = {
                "years": 2,
                "months": 0
            }
            response = authorized_client_user1.put("/admins/ban/users/9999", json=update_data)  # Assuming this ID does not exist
            assert response.status_code == status.HTTP_404_NOT_FOUND
        
        def test_update_ban_user_with_invalid_ban_date(self, test_banned_user, authorized_client_user1):
            update_data = {
                "years": -1,
                "months": 0
            }
            response = authorized_client_user1.put(f"/admins/ban/users/{test_banned_user['ban']['id']}", json=update_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        
        def test_update_ban_user_with_expired_ban(self, test_banned_user_expired, authorized_client_user1):
            update_data = {
                "years": 1,
                "months": 0
            }
            response = authorized_client_user1.put(f"/admins/ban/users/{test_banned_user_expired['ban']['id']}", json=update_data)
            assert response.status_code == status.HTTP_200_OK
            updated_ban = BanUserResponse(**response.json())
            assert updated_ban.email == test_banned_user_expired["user"]["email"]

    class TestUser_BanUserDelete:
        def test_delete_ban_user_as_admin(self, test_banned_user, authorized_client_user1):
            response = authorized_client_user1.delete(f"/admins/ban/users/{test_banned_user['ban']['id']}")
            assert response.status_code == status.HTTP_204_NO_CONTENT
        
        def test_delete_ban_user_as_non_admin(self, test_banned_user, authorized_client_user2):
            response = authorized_client_user2.delete(f"/admins/ban/users/{test_banned_user['ban']['id']}")
            assert response.status_code == status.HTTP_403_FORBIDDEN
        
        def test_delete_nonexistent_ban_user(self, authorized_client_user1):
            response = authorized_client_user1.delete("/admins/ban/users/9999")  # Assuming this ID does not exist
            assert response.status_code == status.HTTP_404_NOT_FOUND