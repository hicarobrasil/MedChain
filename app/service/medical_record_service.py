"""
Servico para gerenciamento de registros medicos.
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.models.medical_record import MedicalRecordModel
from app.blockchain.solana_client import SolanaHashStorage
from app.storage.aws_client import S3Client


class MedicalRecordService:
    def __init__(self, db: Session):
        self.db = db
        self.solana_client = SolanaHashStorage()
        self.s3_client = S3Client()

    def create_medical_record(self, data: Dict[str, Any], file=None) -> MedicalRecordModel:
        """
        Cria um novo registro medico e o armazena na blockchain.

        Args:
            data: Dados do registro medico
            file: Arquivo opcional do pedido medico

        Returns:
            Objeto MedicalRecordModel criado
        """
        # Criar o registro no banco de dados
        record = MedicalRecordModel(
            patient_id=data.get("patient_id"),
            doctor_id=data.get("doctor_id"),
        )

        # Salvar o registro no banco de dados para obter o ID
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        # Armazenar o hash na blockchain
        try:
            # Simplificado para os campos existentes no model
            record_hash = self.solana_client.hash_file(str(record.public_id).encode())
            tx_id = self.solana_client.store_file_hash(str(record.id), record_hash)
            record.blockchain_tx_id = tx_id
            self.db.commit()
        except Exception as e:
            # Log do erro e continuar sem interromper o fluxo
            print(f"Erro ao armazenar na blockchain: {str(e)}")

        return record

    def get_medical_record(self, record_id: int) -> Optional[MedicalRecordModel]:
        """Busca um registro medico pelo ID."""
        record = (
            self.db.query(MedicalRecordModel).filter(MedicalRecordModel.id == record_id).first()
        )
        return record

    def get_medical_records_by_patient(self, patient_id: str) -> List[MedicalRecordModel]:
        """Busca todos os registros medicos de um paciente."""
        return (
            self.db.query(MedicalRecordModel)
            .filter(MedicalRecordModel.patient_id == patient_id)
            .order_by(MedicalRecordModel.created_date.desc())
            .all()
        )

    def get_medical_records_by_doctor(self, doctor_id: str) -> List[MedicalRecordModel]:
        """Busca todos os registros medicos de um medico."""
        return (
            self.db.query(MedicalRecordModel)
            .filter(MedicalRecordModel.doctor_id == doctor_id)
            .order_by(MedicalRecordModel.created_date.desc())
            .all()
        )

    def get_all_medical_records(
        self, skip: int = 0, limit: int = 100
    ) -> List[MedicalRecordModel]:
        """Busca todos os registros medicos com paginacao."""
        return self.db.query(MedicalRecordModel).offset(skip).limit(limit).all()
