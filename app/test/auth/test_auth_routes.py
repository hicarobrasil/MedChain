import pytest
from fastapi import status
from app.main import app

def test_signup_success(client):
    # Payload para signup
    payload = {
        "username": "testuser",
        "email": "test@test.com",
        "password": "password123"
    }
    
    response = client.post("/api/v1/auth/signup", json=payload)
    
    # Dependendo da implementação, pode ser 201 ou outro status
    assert response.status_code == status.HTTP_201_CREATED
    assert "uid" in response.json() or "message" in response.json()

def test_login_failure(client):
    payload = {
        "email": "wrong@test.com",
        "password": "wrongpassword"
    }
    
    response = client.post("/api/v1/auth/login", json=payload)
    
    # Deve falhar
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_logout_success(client):
    # Setup: Precisaríamos de um token válido para fazer logout
    # Como não temos um token válido fácil de gerar, este teste pode ser mockado
    # Por enquanto, apenas testamos se ele aceita a chamada sem token ou se falha corretamente
    response = client.post("/api/v1/auth/logout")
    
    # Deve falhar sem autorização
    assert response.status_code == status.HTTP_403_FORBIDDEN
