import pytest
from fastapi.testclient import TestClient

from app.main import app, get_db
from app.database import SessionLocal
from app.models import User


def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def clean_users_table():
    db = SessionLocal()
    db.query(User).delete()
    db.commit()
    db.close()

@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def register_user(client, username="testuser", password="password123"):
    return client.post(
        "/auth/register",
        json={"username": username, "password": password}
    )


def login_user(client, username="testuser", password="password123"):
    return client.post(
        "/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

@pytest.mark.asyncio
async def test_register_user_success(client):
    response = register_user(client)
    assert response.status_code == 201
    assert response.json()["message"] == "Registration Successful"

@pytest.mark.asyncio
async def test_login_success(client):
    register_user(client)

    response = login_user(client)
    assert response.status_code == 200

    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_wrong_password(client):
    register_user(client)

    response = login_user(client, password="wrongpassword")
    assert response.status_code == 401
    assert "Could not validate user" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    response = login_user(client, username="ghost", password="123")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_change_password_success(client):
    register_user(client)
    token_response = login_user(client)
    token = token_response.json()["access_token"]

    response = client.put(
        "/auth/password",
        json={
            "password": "password123",
            "new_password": "newpass456"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 204

    old_login = login_user(client, password="password123")
    assert old_login.status_code == 401

    new_login = login_user(client, password="newpass456")
    assert new_login.status_code == 200

@pytest.mark.asyncio
async def test_change_password_wrong_current_password(client):
    register_user(client)
    token = login_user(client).json()["access_token"]

    response = client.put(
        "/auth/password",
        json={
            "password": "wrongpassword",
            "new_password": "newpass456"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401
    assert "Incorrect password" in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_user_success(client):
    register_user(client)
    token = login_user(client).json()["access_token"]

    response = client.request(
        "DELETE",
        "/auth/delete",
        json={"password": "password123"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 204

    login_again = login_user(client)
    assert login_again.status_code == 401

@pytest.mark.asyncio
async def test_delete_user_wrong_password(client):
    register_user(client)
    token = login_user(client).json()["access_token"]

    response = client.request(
        "DELETE",
        "/auth/delete",
        json={"password": "wrongpassword"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404
    assert "Incorrect password" in response.json()["detail"]

@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client):
    response = client.put(
        "/auth/password",
        json={
            "password": "password123",
            "new_password": "newpass456"
        }
    )
    assert response.status_code == 401