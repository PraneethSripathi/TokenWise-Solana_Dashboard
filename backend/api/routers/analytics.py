
import traceback
from fastapi import APIRouter, HTTPException
from core.logger import logger
from services import db_service
from core.config import settings
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/analytics/dashboard")
async def get_dashboard_data():
    try:
        total_wallets = await db_service.count_total_wallets()
        total_tx = await db_service.count_total_transactions()
        buy_count = await db_service.count_buy_transactions()
        sell_count = await db_service.count_sell_transactions()
        
        recent_tx = await db_service.get_recent_transactions(limit=20)
        protocol_stats = await db_service.get_protocol_stats()
        active_wallets_raw = await db_service.get_active_wallets_stats(limit=10)
        active_wallets = [{"wallet_address": w["_id"], "tx_count": w["tx_count"]} for w in active_wallets_raw]
        
        holders_data_raw = await db_service.get_token_holder_snapshot(settings.TOKEN_CONTRACT)
        top_holders = []
        holder_count = 0
        if holders_data_raw:
            top_holders = [h.model_dump(by_alias=True) for h in holders_data_raw.holders[:10]]
            holder_count = holders_data_raw.holder_count

        return {
            "total_wallets": total_wallets,
            "total_transactions": total_tx,
            "buy_count": buy_count,
            "sell_count": sell_count,
            "buy_sell_ratio": round(buy_count / max(sell_count, 1), 2),
            "recent_transactions": [tx.model_dump(by_alias=True) for tx in recent_tx],
            "protocol_usage": protocol_stats,
            "most_active_wallets": active_wallets,
            "top_token_holders": top_holders,
            "monitoring_active": True, # Always true if server is running and monitoring task started
            "connected_clients": 0, # This would need to come from the WebSocketManager
            "holder_count": holder_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error in /analytics/dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error – check server log")
    
@router.get("/analytics/protocols")
async def get_protocol_analytics():
    try:
        protocol_stats = await db_service.get_protocol_stats()
        
        yesterday = datetime.utcnow() - timedelta(days=1)
        hourly_stats = await db_service.db.realtime_transactions.aggregate([
            {"$match": {"timestamp": {"$gte": yesterday}}},
            {"$group": {
                "_id": {
                    "protocol": "$protocol",
                    "hour": {"$dateToString": {"format": "%Y-%m-%d %H:00", "date": "$timestamp"}}
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.hour": 1}}
        ]).to_list(1000)
        return {"protocol_stats": protocol_stats, "hourly_breakdown": hourly_stats, "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Error getting protocol analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/volume")
async def get_volume_analytics():
    try:
        yesterday = datetime.utcnow() - timedelta(days=1)
        volume_stats = await db_service.db.realtime_transactions.aggregate([
            {"$match": {"timestamp": {"$gte": yesterday}}},
            {"$group": {
                "_id": None,
                "total_volume": {"$sum": "$amount"},
                "buy_volume": {"$sum": {"$cond": [{"$eq": ["$action_type", "buy"]}, "$amount", 0]}},
                "sell_volume": {"$sum": {"$cond": [{"$eq": ["$action_type", "sell"]}, "$amount", 0]}},
                "transaction_count": {"$sum": 1}
            }}
        ]).to_list(1)
        hourly_volume = await db_service.db.realtime_transactions.aggregate([
            {"$match": {"timestamp": {"$gte": yesterday}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d %H:00", "date": "$timestamp"}},
                "volume": {"$sum": "$amount"},
                "transactions": {"$sum": 1},
                "buy_volume": {"$sum": {"$cond": [{"$eq": ["$action_type", "buy"]}, "$amount", 0]}},
                "sell_volume": {"$sum": {"$cond": [{"$eq": ["$action_type", "sell"]}, "$amount", 0]}}
            }},
            {"$sort": {"_id": 1}}
        ]).to_list(24)
        top_volume_wallets = await db_service.db.realtime_transactions.aggregate([
            {"$match": {"timestamp": {"$gte": yesterday}}},
            {"$group": {
                "_id": "$wallet",
                "total_volume": {"$sum": "$amount"},
                "transaction_count": {"$sum": 1}
            }},
            {"$sort": {"total_volume": -1}},
            {"$limit": 20}
        ]).to_list(20)
        volume_data = volume_stats[0] if volume_stats else {"total_volume": 0, "buy_volume": 0, "sell_volume": 0, "transaction_count": 0}
        return {
            "volume_24h": volume_data,
            "hourly_breakdown": hourly_volume,
            "top_volume_wallets": top_volume_wallets,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting volume analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))