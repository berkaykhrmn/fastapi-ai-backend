import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app, get_db, ai_platform
from app.database import SessionLocal

def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"API status": "Running"}

@pytest.mark.asyncio
async def test_chat_endpoint_success(client, mocker):
    mock_response = "Hello! How can I help you?"
    mocker.patch.object(ai_platform, "chat", return_value=mock_response)
    response = client.post(
        "/chat",
        json={"prompt": "Hello, how are you?"}
    )
    assert response.status_code == 200
    assert response.json()["response"] == mock_response

@pytest.mark.asyncio
async def test_chat_empty_prompt(client):
    response = client.post(
        "/chat",
        json={"prompt": "   "}
    )
    assert response.status_code in (200, 422)

@pytest.mark.asyncio
async def test_translate_success(client, mocker):
    mock_translate = "Hello, how are you?"
    mocker.patch.object(ai_platform, "translate", return_value=mock_translate)
    mocker.patch.object(ai_platform, "detect_language", return_value="tr")
    response = client.post(
        "/chat/translate",
        data={
            "prompt": "Merhaba nasılsın?",
            "target_language": "en"
        }
    )
    assert response.status_code == 200
    assert "translated_text" in response.json()
    assert response.json()["translated_text"] == mock_translate

@pytest.mark.asyncio
async def test_translate_unsupported_language(client, mocker):
    mocker.patch.object(ai_platform, "detect_language", return_value="en")
    response = client.post(
        "/chat/translate",
        data={
            "prompt": "test",
            "target_language": "xx"
        }
    )
    assert response.status_code == 400
    assert "Invalid target language" in response.json()["detail"]

@pytest.mark.asyncio
async def test_translate_same_language(client, mocker):
    mocker.patch.object(ai_platform, "detect_language", return_value="en")

    response = client.post(
        "/chat/translate",
        data={
            "prompt": "Hello world",
            "target_language": "en"
        }
    )
    assert response.status_code == 400
    assert "different from the source language" in response.json()["detail"]