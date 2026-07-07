import pytest
import uuid
from app.models.medical_record import MedicalRecordModel
from sqlalchemy.exc import IntegrityError

class TestMedicalRecordModel:

    def test_medical_record_default_values(self, db_session):
        """
        Test Case 1 (Campos do Model): Valide as restrições do MedicalRecordModel, 
        garantindo que o campo blockchain_tx_id aceite valores nulos/vazios por padrão.
        """
        record = MedicalRecordModel(
            public_id=uuid.uuid4(),
            doctor_id=uuid.uuid4(),
            patient_id=uuid.uuid4(),
            hash="some_hash_123"
        )
        db_session.add(record)
        db_session.commit()
        
        # Verificações
        assert record.blockchain_tx_id is None
        assert isinstance(record.id, int)
        assert isinstance(record.public_id, uuid.UUID)

    def test_medical_record_update_blockchain_id(self, db_session):
        """
        Valida que o campo blockchain_tx_id armazena strings corretamente após a atualização.
        """
        record = MedicalRecordModel(
            public_id=uuid.uuid4(),
            doctor_id=uuid.uuid4(),
            patient_id=uuid.uuid4(),
            hash="some_hash_456"
        )
        db_session.add(record)
        db_session.commit()
        
        # Atualização
        tx_id = "5H6p..." # Simulação de ID da Solana
        record.blockchain_tx_id = tx_id
        db_session.commit()
        
        # Verificações
        db_session.refresh(record)
        assert record.blockchain_tx_id == tx_id

    def test_medical_record_hash_uniqueness(self, db_session):
        """
        Valida que o campo hash é único (conforme definido no model).
        """
        common_hash = "unique_hash_789"
        
        record1 = MedicalRecordModel(
            public_id=uuid.uuid4(),
            doctor_id=uuid.uuid4(),
            patient_id=uuid.uuid4(),
            hash=common_hash
        )
        db_session.add(record1)
        db_session.commit()
        
        record2 = MedicalRecordModel(
            public_id=uuid.uuid4(),
            doctor_id=uuid.uuid4(),
            patient_id=uuid.uuid4(),
            hash=common_hash
        )
        db_session.add(record2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
