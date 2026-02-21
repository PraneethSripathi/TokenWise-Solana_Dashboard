# your_project_name/services/wallet_discovery.py
from collections import defaultdict
from core.logger import logger
from core.config import settings
from models.pydantic_models import TokenHolder, TokenHolderSnapshot, WalletTracker
from services import solana_rpc, db_service
from fastapi import HTTPException
from datetime import datetime
import traceback

# Program ID for SPL Token Program (constant)
SPL_TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5mW"

async def discover_top_wallets(mint_address: str, top_n: int = 100):
    logger.info(f"Discovering top {top_n} wallets for mint: {mint_address}")

    params = [
        SPL_TOKEN_PROGRAM_ID,
        {
            "encoding": "jsonParsed",
            "filters": [
                {"memcmp": {"offset": 0, "bytes": mint_address}}
            ],
            "commitment": "confirmed"
        }
    ]

    try:
        accounts_data = await solana_rpc.call_solana_rpc("getProgramAccounts", params)
        if not accounts_data:
            logger.warning(f"No token accounts found for mint {mint_address} from RPC. Relying on seeded data if available.")
            return

        supply_info = await solana_rpc.get_token_supply(mint_address)
        token_decimals = 0
        if supply_info and supply_info.get("value"):
            token_decimals = int(supply_info["value"].get("decimals", 0))

        owner_balances = defaultdict(float)
        owner_token_accounts = {} # Maps owner wallet to one of their associated token accounts

        for account in accounts_data:
            pubkey = account['pubkey']
            account_info = account['account']['data']['parsed']['info']
            owner = account_info['owner']
            token_amount_raw = int(account_info['tokenAmount']['amount'])
            
            ui_amount = float(token_amount_raw) / (10**token_decimals)

            if owner and ui_amount > 0:
                owner_balances[owner] += ui_amount
                # Store one of the associated token accounts for this owner
                if owner not in owner_token_accounts:
                    owner_token_accounts[owner] = pubkey

        aggregated_holders = []
        for owner, balance in owner_balances.items():
            if balance > 0:
                aggregated_holders.append(TokenHolder(
                    owner=owner,
                    address=owner_token_accounts.get(owner, owner), # Use token account or owner address
                    balance=balance,
                    ui_amount=balance,
                    decimals=token_decimals
                ))
        
        sorted_holders = sorted(aggregated_holders, key=lambda x: x.balance, reverse=True)
        top_n_holders = sorted_holders[:top_n]

        current_total_supply = 0.0
        if supply_info and supply_info.get("value"):
            current_total_supply = supply_info["value"]["uiAmount"]

        snapshot = TokenHolderSnapshot(
            token_address=mint_address,
            holders=top_n_holders, # Pass Pydantic models directly
            total_supply=current_total_supply,
            holder_count=len(top_n_holders),
            last_updated=datetime.utcnow()
        )
        await db_service.update_token_holder_snapshot(snapshot)

        for holder_model in top_n_holders:
            wallet_address = holder_model.owner
            wallet_tracker = WalletTracker(
                address=wallet_address,
                balance=holder_model.balance, # Can update current token amount
                token_amount=holder_model.balance, # Redundant with balance, consider removing one.
                # If balance is for SOL and token_amount for the specific token, keep both.
                # Otherwise, consider combining or clarifying.
                # For now, assigning both based on the original code
            )
            await db_service.update_or_insert_wallet_tracker(wallet_tracker)
            
        logger.info(f"✅ Discovered and tracking {len(top_n_holders)} wallets using getProgramAccounts.")

    except HTTPException as e:
        logger.error(f"Failed to discover top wallets (HTTPException): {e.detail}. Relying on seeded data if available.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during top wallet discovery: {e}\n{traceback.format_exc()}. Relying on seeded data if available.")