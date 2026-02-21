
from core.database import db
from core.logger import logger
from models.pydantic_models import RealtimeTransaction, WalletTracker, TokenHolderSnapshot, TokenHolder
from typing import List, Dict, Any,Optional

def _convert_mongo_doc_id(doc: Dict[str, Any]) -> Dict[str, Any]:
    if doc and '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc

async def insert_realtime_transaction(tx: RealtimeTransaction):
    try:
        # Pydantic's model_dump(by_alias=True) handles conversion for insertion
        await db.realtime_transactions.insert_one(tx.model_dump(by_alias=True))
        return True
    except Exception as e:
        logger.error(f"Error inserting transaction: {e}", exc_info=True)
        return False

async def get_recent_transactions(limit: int = 20) -> List[RealtimeTransaction]:
    try:
        # Apply conversion here
        tx_data = await db.realtime_transactions.find().sort("timestamp", -1).limit(limit).to_list(limit)
        return [RealtimeTransaction(**_convert_mongo_doc_id(doc)) for doc in tx_data]
    except Exception as e:
        logger.error(f"Error fetching recent transactions: {e}", exc_info=True)
        return []

async def get_protocol_stats() -> List[Dict[str, Any]]:
    try:
        return await db.realtime_transactions.aggregate([
            {"$group": {"_id": "$protocol", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]).to_list(10)
    except Exception as e:
        logger.error(f"Error fetching protocol stats: {e}", exc_info=True)
        return []

async def get_active_wallets_stats(limit: int = 10) -> List[Dict[str, Any]]:
    try:
        return await db.realtime_transactions.aggregate([
            {"$group": {"_id": "$wallet", "tx_count": {"$sum": 1}}},
            {"$sort": {"tx_count": -1}},
            {"$limit": limit}
        ]).to_list(limit)
    except Exception as e:
        logger.error(f"Error fetching active wallets: {e}", exc_info=True)
        return []

async def get_token_holder_snapshot(token_address: str) -> Optional[TokenHolderSnapshot]:
    try:
        # Apply conversion here
        holders_data = await db.token_holders.find_one({"token_address": token_address})
        if holders_data:
            return TokenHolderSnapshot(**_convert_mongo_doc_id(holders_data))
        return None
    except Exception as e:
        logger.error(f"Error fetching token holder snapshot: {e}", exc_info=True)
        return None

async def update_token_holder_snapshot(snapshot: TokenHolderSnapshot):
    try:
        
        await db.token_holders.update_one(
            {"token_address": snapshot.token_address},
            {"$set": snapshot.model_dump(by_alias=True)},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Error updating token holder snapshot: {e}", exc_info=True)
        return False

async def get_tracked_wallets_from_db(limit: int = 1000) -> List[WalletTracker]:
    try:
        
        wallets_data = await db.wallets.find({"active": True}).to_list(limit)
        return [WalletTracker(**_convert_mongo_doc_id(doc)) for doc in wallets_data]
    except Exception as e:
        logger.error(f"Error loading tracked wallets from DB: {e}", exc_info=True)
        return []

async def update_or_insert_wallet_tracker(wallet: WalletTracker):
    try:
        
        await db.wallets.update_one(
            {"address": wallet.address},
            {"$set": wallet.model_dump(by_alias=True)},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Error updating/inserting wallet tracker: {e}", exc_info=True)
        return False
 
async def count_total_wallets() -> int:
    try:
        return await db.wallets.count_documents({"active": True})
    except Exception as e:
        logger.error(f"Error counting total wallets: {e}", exc_info=True)
        return 0

async def count_total_transactions() -> int:
    try:
        return await db.realtime_transactions.count_documents({})
    except Exception as e:
        logger.error(f"Error counting total transactions: {e}", exc_info=True)
        return 0

async def count_buy_transactions() -> int:
    try:
        return await db.realtime_transactions.count_documents({"action_type": "buy"})
    except Exception as e:
        logger.error(f"Error counting buy transactions: {e}", exc_info=True)
        return 0

async def count_sell_transactions() -> int:
    try:
        return await db.realtime_transactions.count_documents({"action_type": "sell"})
    except Exception as e:
        logger.error(f"Error counting sell transactions: {e}", exc_info=True)
        return 0