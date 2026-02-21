
from fastapi import APIRouter, HTTPException
from core.logger import logger
from services import db_service
from datetime import datetime, timedelta
from api.websocket_manager import manager

router = APIRouter()

@router.get("/status")
async def get_status():
    return {
        "status": "online",
        "monitoring_active": manager.is_monitoring,
        "connected_clients": len(manager.active_connections),
        "tracked_wallets": len(manager.tracked_wallets),
        "last_discovery_run": manager.last_discovery_run.isoformat() if manager.last_discovery_run else "N/A",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/realtime/status") 
async def get_realtime_status():
    try:
        last_hour = datetime.utcnow() - timedelta(hours=1)
        recent_tx_count = await db_service.db.realtime_transactions.count_documents({"timestamp": {"$gte": last_hour}})
        return {
            "monitoring_active": manager.is_monitoring,
            "connected_clients": len(manager.active_connections),
            "tracked_wallets": len(manager.tracked_wallets),
            "monitored_token": manager.TOKEN_CONTRACT, # Use manager's token_contract
            "recent_transactions_1h": recent_tx_count,
            "last_processed_slot": manager.last_processed_slot,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting real-time status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/token-holders/{mint_address}")
async def get_token_holders(mint_address: str):
    try:
        logger.info(f"Attempting to fetch token holders for mint: {mint_address} from MongoDB.")
        snapshot_model = await db_service.get_token_holder_snapshot(mint_address)
        
        if snapshot_model:
            logger.info(f"Found token holders data in DB for {mint_address}. Holder count: {snapshot_model.holder_count}")
            return [h.model_dump(by_alias=True) for h in snapshot_model.holders]
        else:
            logger.warning(f"No token holders snapshot found in DB for mint: {mint_address}.")
            raise HTTPException(status_code=404, detail="Token holders snapshot not found for this mint.")
    except HTTPException as e:
        raise e # Re-raise FastAPI HTTPExceptions
    except Exception as e:
        logger.error(f"Error getting token holders from DB for {mint_address}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve token holders.")

@router.get("/wallets/{wallet_address}/transactions")
async def get_wallet_transactions(wallet_address: str, limit: int = 20):
    try:
        transactions = await db_service.db.realtime_transactions.find({"wallet": wallet_address}).sort("timestamp", -1).limit(limit).to_list(limit)
        
        protocol_stats_wallet = await db_service.db.realtime_transactions.aggregate([
            {"$match": {"wallet": wallet_address}},
            {"$group": {"_id": "$protocol", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]).to_list(10)

        return {
            "wallet_address": wallet_address,
            "transactions": [tx.model_dump(by_alias=True) for tx in transactions], # Ensure proper Pydantic conversion
            "protocol_usage": {p["_id"]: p["count"] for p in protocol_stats_wallet}
        }
    except Exception as e:
        logger.error(f"Error fetching transactions for wallet {wallet_address}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve wallet transactions.")

@router.post("/realtime/start-monitoring")
async def start_realtime_monitoring():
    try:
        await manager.start_monitoring()
        return {"status": "success", "message": "Real-time monitoring started."}
    except Exception as e:
        logger.error(f"Failed to start monitoring via API: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start monitoring.")

# You might also want a stop endpoint
@router.post("/realtime/stop-monitoring")
async def stop_realtime_monitoring():
    try:
        await manager.stop_monitoring()
        return {"status": "success", "message": "Real-time monitoring stopped."}
    except Exception as e:
        logger.error(f"Failed to stop monitoring via API: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to stop monitoring.")