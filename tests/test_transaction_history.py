import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, engine
from app.models import Base

@pytest.fixture(scope="module")
def test_client():
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)
    yield client
    Base.metadata.drop_all(bind=engine)

def test_get_transaction_history(test_client):
    # Регистрация пользователя
    test_client.post("/register/", json={"username": "testuser", "password": "testpassword"})
    # Логин пользователя
    response = test_client.post("/login/", json={"username": "testuser", "password": "testpassword"})
    token = response.json()["access_token"]
    # Получение истории транзакций
    response = test_client.get("/transaction_history/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) == 0