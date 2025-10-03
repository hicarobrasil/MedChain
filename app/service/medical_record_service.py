"""
Serviço para gerenciamento de registros médicos.
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.models.medical_record import MedicalRecord
from app.blockchain.solana_client import SolanaHashStorage
from app.storage.aws_client import S3Client


class MedicalRecordService:
    def __init__(self, db: Session):
        self.db = db
        self.solana_client = SolanaHashStorage()
        self.s3_client = S3Client()

    def create_medical_record(self, data: Dict[str, Any], file=None) -> MedicalRecord:
        """
        Cria um novo registro médico e o armazena na blockchain.

        Args:
            data: Dados do registro médico
            file: Arquivo opcional do pedido médico

        Returns:
            Objeto MedicalRecord criado
        """
        # Criar o registro no banco de dados
        record = MedicalRecord(
            patient_id=data.get("patient_id"),
            doctor_id=data.get("doctor_id"),
            description=data.get("description"),
            medications=data.get("medications", []),
        )

        # Se um arquivo foi fornecido, fazer upload para o S3
        # if file:
        #     file_url, file_hash = self.s3_client.upload_file(
        #         file, f"medical_records/{record.patient_id}/{record.id}_{file.filename}"
        #     )
        #     record.file_url = file_url
        #     record.file_hash = file_hash

        # Salvar o registro no banco de dados para obter o ID
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        # Calcular o hash dos dados sensíveis
        record_hash = self.solana_client.hash_file(record.sensitive_data())
        record.record_hash = record_hash

        # Armazenar o hash na blockchain
        try:
            tx_id = self.solana_client.store_file_hash(str(record.id), record_hash)
            record.blockchain_tx_id = tx_id
            record.blockchain_verified = True
            self.db.commit()
        except Exception as e:
            # Log do erro e continuar sem interromper o fluxo
            print(f"Erro ao armazenar na blockchain: {str(e)}")
            # Poderia implementar um sistema de retry aqui

        return record

    def get_medical_record(self, record_id: int) -> Optional[MedicalRecord]:
        """Busca um registro médico pelo ID."""
        record = (
            self.db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
        )

        # Se encontrou e tem ID de transação, verificar na blockchain
        if record and record.blockchain_tx_id:
            try:
                verified = self.solana_client.verify_file(
                    str(record.id), record.sensitive_data(), record.blockchain_tx_id
                )
                # Atualizar status de verificação
                if record.blockchain_verified != verified:
                    record.blockchain_verified = verified
                    self.db.commit()
            except Exception as e:
                print(f"Erro ao verificar na blockchain: {str(e)}")

        return record

    def get_medical_records_by_patient(self, patient_id: str) -> List[MedicalRecord]:
        """Busca todos os registros médicos de um paciente."""
        return (
            self.db.query(MedicalRecord)
            .filter(MedicalRecord.patient_id == patient_id)
            .order_by(MedicalRecord.date_created.desc())
            .all()
        )

    def get_medical_records_by_doctor(self, doctor_id: str) -> List[MedicalRecord]:
        """Busca todos os registros médicos de um médico."""
        return (
            self.db.query(MedicalRecord)
            .filter(MedicalRecord.doctor_id == doctor_id)
            .order_by(MedicalRecord.date_created.desc())
            .all()
        )

    def get_all_medical_records(
        self, skip: int = 0, limit: int = 100
    ) -> List[MedicalRecord]:
        """Busca todos os registros médicos com paginação."""
        return self.db.query(MedicalRecord).offset(skip).limit(limit).all()

    def get_patient_medical_records(self, patient_id) -> List[MedicalRecord]:
        """Busca todos os registros médicos de um paciente."""
        return (
            self.db.query(MedicalRecord)
            .filter(MedicalRecord.patient_id == patient_id)
            .order_by(MedicalRecord.date_created.desc())
            .all()
        )

    def get_doctor_medical_records(self, doctor_id) -> List[MedicalRecord]:
        """Busca todos os registros médicos de um médico."""
        return (
            self.db.query(MedicalRecord)
            .filter(MedicalRecord.doctor_id == doctor_id)
            .order_by(MedicalRecord.date_created.desc())
            .all()
        )
