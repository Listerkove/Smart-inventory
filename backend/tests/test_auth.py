import pytest

def test_register(client, db_session):
    response = client.post("/auth/register", json={
        "username": "newuser",
        "email": "new@example.com",
        "password": "secret123",  # meets length requirement
        "role": "manager"
    })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"

def test_register_duplicate_username(client, sample_admin):
    user_id, username, password = sample_admin
    response = client.post("/auth/register", json={
        "username": username,
        "email": "another@example.com",
        "password": "validpass123",  # valid password
    })
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()

def test_login_success(client, sample_admin):
    user_id, username, password = sample_admin
    response = client.post("/auth/login", json={
        "username": username,
        "password": password
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

def test_login_wrong_password(client, sample_admin):
    user_id, username, password = sample_admin
    response = client.post("/auth/login", json={
        "username": username,
        "password": "wrongpass"
    })
    assert response.status_code == 401

def test_get_me(client, auth_headers_admin, sample_admin):
    user_id, username, password = sample_admin
    response = client.get("/auth/me", headers=auth_headers_admin)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == username