import pytest
from unittest.mock import MagicMock, patch
from jwt import ExpiredSignatureError, InvalidTokenError
from app.auth.service import SessionDataSource, UserTokenService
from app.models.login_record import User
from app.auth.schemas import UserCreateModel

class TestAuthService:

    @pytest.fixture
    def user_service(self):
        return UserTokenService()

    def test_session_data_source_get_token_success(self, monkeypatch):
        # Mock decode_jwt
        monkeypatch.setattr("app.auth.service.decode_jwt", lambda token: {"email": "test@test.com"})
        
        token_data = SessionDataSource.get_token("valid_token")
        assert token_data["email"] == "test@test.com"

    def test_session_data_source_get_token_expired(self, monkeypatch):
        # Mock decode_jwt to raise ExpiredSignatureError
        monkeypatch.setattr("app.auth.service.decode_jwt", MagicMock(side_effect=ExpiredSignatureError))
        
        with pytest.raises(ExpiredSignatureError):
            SessionDataSource.get_token("expired_token")

    def test_user_token_service_get_user_by_email(self, user_service, db_session):
        mock_user = User(email="test@test.com")
        
        # Mock the db.query
        db_session.query = MagicMock()
        db_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        user = user_service.get_user_by_email("test@test.com", db_session)
        assert user.email == "test@test.com"

    def test_user_token_service_user_exists(self, user_service, db_session):
        # Mock get_user_by_email
        user_service.get_user_by_email = MagicMock(return_value=User(email="test@test.com"))
        
        assert user_service.user_exists("test@test.com", db_session) is True
        
        user_service.get_user_by_email.return_value = None
        assert user_service.user_exists("nonexistent@test.com", db_session) is False

    @patch("app.auth.service.generate_passwd_hash")
    def test_create_user(self, mock_hash, user_service, db_session):
        mock_hash.return_value = "hashed_pw"
        user_data = UserCreateModel(email="new@test.com", password="password", username="newuser")
        
        # Mock db.add, commit, refresh
        db_session.add = MagicMock()
        db_session.commit = MagicMock()
        db_session.refresh = MagicMock()
        
        new_user = user_service.create_user(user_data, db_session)
        
        assert new_user.email == "new@test.com"
        assert new_user.password_hash == "hashed_pw"
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()
