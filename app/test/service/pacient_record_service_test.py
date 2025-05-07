from app.service.pacient_record_service import PacientService
from app.models.pacient_record import PacientRecord
import pytest
from unittest.mock import MagicMock

class TestPacientRecordService:

    def test_create_pacient_record(self, mocker):
        # Mock do banco de dados
        mock_db = mocker.MagicMock()
        service = PacientService(mock_db)

        # Dados simulados
        data = {
            "name": "João da Silva",
            "dateofbirth": "1990-01-01",
            "gender": 1,
            "email": "blabla@gmail.com",
            "phone": "123456789",
            "status": 1,
        }

        pacient = service.create_pacient(data)

        assert pacient is not None
        assert pacient.name == data["name"]
        assert pacient.email == data["email"]
        assert pacient.phone == data["phone"]
        assert pacient.dateofbirth == data["dateofbirth"]
        assert pacient.status == data["status"]
        mock_db.add.assert_called_once_with(pacient)
        mock_db.commit.assert_called_once()

    def test_get_pacient_record(self, mocker):
        # Mock do banco de dados
        mock_db = mocker.MagicMock()
        service = PacientService(mock_db)

        # Dados simulados
        pacient_id = 1
        pacient = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = pacient

        result = service.get_pacient_by_id(pacient_id)

        assert result is not None
        assert result == pacient
        mock_db.query.assert_called_once_with(PacientRecord)
        mock_db.query.return_value.filter.assert_called
