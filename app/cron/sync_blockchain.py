import logging
import sys
import os

# Adiciona o diretório raiz ao path para permitir importações da 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from app.database import Session as SessionLocal
from app.models.medical_record import MedicalRecordModel
from app.service.blockchain_service import BlockchainService

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("blockchain_sync_job")

def sync_medical_records_to_blockchain(db: Session = None):
    """
    Sincroniza prontuários médicos sem ID de transação blockchain com a rede Solana.
    """
    logger.info("Iniciando job de sincronização blockchain...")
    
    # Se não for fornecida uma sessão, cria uma nova
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True
        
    blockchain_service = BlockchainService()
    
    try:
        # a) Buscar no banco de dados todos os registros de MedicalRecordModel onde o campo blockchain_tx_id esteja vazio
        records_to_sync = db.query(MedicalRecordModel).filter(
            (MedicalRecordModel.blockchain_tx_id == None) | (MedicalRecordModel.blockchain_tx_id == "")
        ).all()
        
        if not records_to_sync:
            logger.info("Nenhum prontuário médico pendente de sincronização.")
            return

        logger.info(f"Encontrados {len(records_to_sync)} registros para sincronizar.")

        for record in records_to_sync:
            # b) Para cada registro encontrado, obter o hash do arquivo e chamar a lógica de store_file_hash
            if not record.hash:
                logger.warning(f"Prontuário {record.id} não possui hash. Pulando.")
                continue

            try:
                logger.info(f"Sincronizando registro {record.id} (Public ID: {record.public_id})...")
                
                # Usamos o public_id como identificador na blockchain para rastreabilidade
                tx_id = blockchain_service.store_file_hash(
                    file_hash=record.hash, 
                    file_id=str(record.public_id)
                )
                
                # c) Após o sucesso da transação na Solana, atualizar o respectivo MedicalRecordModel preenchendo o campo blockchain_tx_id
                record.blockchain_tx_id = tx_id
                db.commit()
                logger.info(f"Registro {record.id} sincronizado com sucesso. Tx ID: {tx_id}")
                
            except Exception as e:
                db.rollback()
                logger.error(f"Falha ao sincronizar registro {record.id}: {str(e)}")
                # Continua para o próximo registro
                continue
                
    except Exception as e:
        logger.error(f"Erro durante a execução do job de sincronização: {str(e)}")
    finally:
        # Só fecha se a sessão foi criada internamente
        if own_session:
            db.close()
        logger.info("Job de sincronização finalizado.")

if __name__ == "__main__":
    sync_medical_records_to_blockchain()
