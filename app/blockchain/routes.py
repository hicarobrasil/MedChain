from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.service.blockchain_service import BlockchainService
from typing import Optional

router = APIRouter(tags=["Blockchain"])

class HashStorageRequest(BaseModel):
    file_hash: str
    file_id: Optional[str] = None

class HashStorageResponse(BaseModel):
    blockchain_tx_id: str
    message: str

@router.post("/store-hash", response_model=HashStorageResponse, status_code=status.HTTP_201_CREATED)
async def store_hash(request: HashStorageRequest):
    """
    Endpoint to manually store a file hash on the Solana blockchain.
    """
    service = BlockchainService()
    try:
        tx_id = service.store_file_hash(request.file_hash, request.file_id)
        return HashStorageResponse(
            blockchain_tx_id=tx_id,
            message="Hash successfully stored on Solana"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error storing hash on Solana: {str(e)}"
        )
