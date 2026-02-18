def test_get_users_admin(client, auth_headers_admin):
    response = client.get("/admin/users", headers=auth_headers_admin)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

def test_create_user_admin(client, auth_headers_admin):
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    response = client.post("/admin/users", headers=auth_headers_admin, json={
        "username": f"newadmin_{unique_id}",
        "email": f"newadmin_{unique_id}@example.com",
        "password": "newpass123",      # ensure meets length requirement
        "role": "manager",
        "is_active": True
    })
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == f"newadmin_{unique_id}"

def test_manager_cannot_access_admin(client, auth_headers_manager):
    response = client.get("/admin/users", headers=auth_headers_manager)
    assert response.status_code == 403