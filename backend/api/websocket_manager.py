
import asyncio
import json
import random
import time
import traceback
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import WebSocket, WebSocketDisconnect

from core.logger import logger
from core.database import custom_json_encoder # Ensure this is imported for JSON encoding
from core.config import settings
from models.pydantic_models import RealtimeTransaction, TokenHolderSnapshot, WalletTracker, TokenHolder
from services import db_service, solana_rpc, wallet_discovery

# Constants from original code
PROTOCOL_PROGRAM_IDS = {
    "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB": "Jupiter",
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4": "Jupiter",
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": "Raydium",
    "5quBtoiQqxF9Jv6KYKctB59NT3gtJD2Y65kdnB1Uev3h": "Raydium",
    "27haf8L6oxUeXrHrgEgsexjSY5hbVUWEmvv9Nyxg8vQv": "Raydium",
    "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP": "Orca",
    "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc": "Orca",
    "DjVE6JNiYqPL2QXyCUUh8rNjHrbz9hXHNYt99MQ59qw1": "Orca",
    "SwaPpA9LAaLfeLi3a68M4DjnLqgtticKg6CnyNwgAC8": "Saber",
    "22Y43yTVxuUkoRKdm9thyRhQ3SdgQS7c7kB6UNCiaczD": "Serum",
    "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin": "Serum",
}


class WalletManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.tracked_wallets: Dict[str, Dict[str, Any]] = {}
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.last_discovery_run: Optional[datetime] = None
        self.discovery_interval_seconds = 21600 # 6 hours
        self.last_processed_slot: int = 0
        self.TOKEN_CONTRACT = settings.TOKEN_CONTRACT # Use from settings

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        client_id = str(uuid.uuid4())
        self.active_connections[client_id] = websocket
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")
        return client_id

    async def disconnect(self, websocket: WebSocket):
        client_id_to_remove = None
        for cid, ws in self.active_connections.items():
            if ws == websocket:
                client_id_to_remove = cid
                break
        if client_id_to_remove:
            del self.active_connections[client_id_to_remove]
        logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")
        if not self.active_connections and self.is_monitoring:
            await self.stop_monitoring() # Stop monitoring if no clients are connected

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except RuntimeError as e:
            logger.warning(f"Could not send to WebSocket (likely closed): {e}")
            await self.disconnect(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for websocket in list(self.active_connections.values()): # Iterate over a copy to allow modification during loop
            try:
                await websocket.send_text(message)
            except RuntimeError as e:
                logger.warning(f"Could not send to WebSocket (likely closed): {e}")
                disconnected.append(websocket)
        for ws in disconnected:
            await self.disconnect(ws)
        if disconnected:
            logger.info(f"Disconnected {len(disconnected)} stale WebSocket clients.")

    async def start_monitoring(self):
        if not self.is_monitoring:
            self.is_monitoring = True
            logger.info("Starting wallet monitoring.")
            # Ensure _monitor_wallets_periodically is a background task
            self.monitor_task = asyncio.create_task(self._monitor_wallets_periodically())
        else:
            logger.info("Wallet monitoring is already running.")

    async def stop_monitoring(self):
        if self.is_monitoring:
            self.is_monitoring = False
            if self.monitor_task:
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    logger.info("Wallet monitoring task explicitly cancelled.")
                finally:
                    self.monitor_task = None
            logger.info("Wallet monitoring stopped.")
        else:
            logger.info("Wallet monitoring is not active.")

    async def _monitor_wallets_periodically(self):
        # This will now contain the core logic for fetching and broadcasting real-time data
        while self.is_monitoring:
            try:
                current_time = datetime.utcnow()
                if self.last_discovery_run is None or \
                   (current_time - self.last_discovery_run).total_seconds() >= self.discovery_interval_seconds:
                    logger.info("Initiating scheduled top wallet discovery.")
                    await wallet_discovery.discover_top_wallets(self.TOKEN_CONTRACT)
                    self.last_discovery_run = current_time

                if self.tracked_wallets: # Only generate mocks if there are wallets to track
                    await self._generate_and_broadcast_mock_transaction() # Keep generating mock transactions
                
                await self.broadcast_dashboard_data()

            except asyncio.CancelledError:
                logger.info("Monitoring loop cancelled.")
                break # Exit the loop if cancelled
            except Exception as e:
                logger.error(f"Error in periodic wallet monitoring: {e}\n{traceback.format_exc()}")
            finally:
                await asyncio.sleep(5) # Adjust interval as needed

    async def _generate_and_broadcast_mock_transaction(self):
        if not self.tracked_wallets:
            logger.warning("No tracked wallets available to generate mock transactions.")
            return

        wallet_address = random.choice(list(self.tracked_wallets.keys()))
        
        action_type = random.choice(["buy", "sell"])
        amount = round(random.uniform(10, 1000), 4)
        protocol = random.choice(list(PROTOCOL_PROGRAM_IDS.values())) # Use defined constants
        
        signature = str(uuid.uuid4()).replace('-', '') + str(int(time.time()))
        
        mock_tx = RealtimeTransaction(
            signature=signature,
            timestamp=datetime.utcnow(),
            wallet=wallet_address,
            token_address=self.TOKEN_CONTRACT,
            amount=amount,
            action_type=action_type,
            protocol=protocol,
            block_time=int(time.time()),
            slot=random.randint(100000000, 200000000)
        )

        try:
            await db_service.insert_realtime_transaction(mock_tx)
            logger.info(f"Generated and saved mock transaction: {mock_tx.action_type} {mock_tx.amount} for {mock_tx.wallet[:8]}...")
            
            await self.broadcast(json.dumps({
                "type": "new_transaction",
                "data": mock_tx.model_dump(by_alias=True),
                "timestamp": datetime.utcnow().isoformat()
            }, default=custom_json_encoder))
        except Exception as e:
            logger.error(f"Error generating or saving mock transaction: {e}", exc_info=True)

    async def discover_top_wallets(self, mint_address: str, top_n: int = 100):
        # Delegate to the service function
        await wallet_discovery.discover_top_wallets(mint_address, top_n)
        # After discovery, reload the local tracked_wallets cache
        await self.load_tracked_wallets()

    async def load_tracked_wallets(self):
        try:
            wallets_data = await db_service.get_tracked_wallets_from_db()
            self.tracked_wallets = {wallet.address: wallet.model_dump(by_alias=True) for wallet in wallets_data}
            logger.info(f"📋 Loaded {len(self.tracked_wallets)} tracked wallets from DB into manager cache.")
        except Exception as e:
            logger.error(f"Error loading tracked wallets into manager: {e}", exc_info=True)

    async def broadcast_dashboard_data(self):
        try:
            top_holders_data = await db_service.get_token_holder_snapshot(self.TOKEN_CONTRACT)
            top_holders_list = []
            holder_count = 0
            if top_holders_data:
                top_holders_list = [h.model_dump(by_alias=True) for h in top_holders_data.holders[:10]]
                holder_count = top_holders_data.holder_count

            recent_txns_list = await db_service.get_recent_transactions(limit=20)
            protocol_stats = await db_service.get_protocol_stats()
            active_wallets_raw = await db_service.get_active_wallets_stats(limit=10)
            active_wallets_list = [{"wallet_address": w["_id"], "tx_count": w["tx_count"]} for w in active_wallets_raw]

            dashboard_data = {
                "type": "dashboard_update",
                "monitoring_active": self.is_monitoring,
                "connected_clients": len(self.active_connections),
                "tracked_wallets_count": len(self.tracked_wallets),
                "top_holders": top_holders_list,
                "recent_transactions": [tx.model_dump(by_alias=True) for tx in recent_txns_list],
                "protocol_usage": protocol_stats,
                "most_active_wallets": active_wallets_list,
                "holder_count": holder_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.broadcast(json.dumps(dashboard_data, default=custom_json_encoder))
            logger.info("Dashboard data broadcasted.")
        except Exception as e:
            logger.error(f"Error broadcasting dashboard data: {e}\n{traceback.format_exc()}")

    async def websocket_endpoint(self, websocket: WebSocket):
        """This method will be directly mapped to the FastAPI websocket route."""
        client_id = await self.connect(websocket)
        try:
            await self.send_personal_message(json.dumps({
                "type": "connection_established",
                "message": "Connected to TokenWise real-time feed",
                "monitoring_token": self.TOKEN_CONTRACT,
                "tracked_wallets": len(self.tracked_wallets),
                "timestamp": datetime.utcnow().isoformat()
            }), websocket)
            while True:
                try:
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    if message:
                        data = json.loads(message)
                        cmd = data.get("command")
                        if cmd == "ping":
                            await self.send_personal_message(json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()}), websocket)
                        elif cmd == "get_status":
                            await self.send_personal_message(json.dumps({
                                "type": "status",
                                "monitoring_active": self.is_monitoring,
                                "connected_clients": len(self.active_connections),
                                "tracked_wallets": len(self.tracked_wallets),
                                "timestamp": datetime.utcnow().isoformat()
                            }), websocket)
                        elif cmd == "get_recent_transactions":
                            limit = data.get("limit", 10)
                            recent_data = await db_service.get_recent_transactions(limit)
                            await self.send_personal_message(json.dumps({
                                "type": "recent_transactions",
                                "transactions": [tx.model_dump(by_alias=True) for tx in recent_data],
                                "timestamp": datetime.utcnow().isoformat()
                            }, default=custom_json_encoder), websocket)
                except asyncio.TimeoutError:
                    await self.send_personal_message(json.dumps({"type": "keepalive", "timestamp": datetime.utcnow().isoformat()}), websocket)
        except WebSocketDisconnect:
            logger.info(f"WebSocket client {client_id} disconnected normally.")
        except Exception as e:
            logger.error(f"WebSocket error for client {client_id}: {e}", exc_info=True)
        finally:
            await self.disconnect(websocket)

manager = WalletManager() # Instantiate the manager once