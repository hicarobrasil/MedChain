import pytest
from fastapi import status
from app.models.login_record import User
from app.auth.utils import make_password

def test_signup_email_exists(client, db_session):
    # Setup: Criar usuário existente na tabela de autenticação
    hashed_password = make_password("hash")
    user = User(username="existinguser", email="exist@test.com", password_hash=hashed_password, role="user")
    db_session.add(user)
    db_session.commit()
    
    # Tentar registrar com mesmo email
    payload = {
        "username": "newuser",
        "email": "exist@test.com",
        "password": "password123"
    }
    
    response = client.post("/api/v1/auth/signup", json=payload)
    
    assert response.status_code == status.HTTP_409_CONFLICT
    # Ajuste a mensagem conforme a implementação real se necessário
    assert "detail" in response.json()

def test_login_invalid_password(client, db_session):
    # Setup: Criar usuário
    hashed_password = make_password("correctpassword")
    user = User(username="loginuser", email="login_fail@test.com", password_hash=hashed_password, role="user")
    db_session.add(user)
    db_session.commit()
    
    payload = {
        "email": "login_fail@test.com",
        "password": "wrongpassword"
    }
    
    response = client.post("/api/v1/auth/login", json=payload)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
