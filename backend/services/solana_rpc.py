

import asyncio
import aiohttp
import traceback
from fastapi import HTTPException
from core.logger import logger
from core.config import settings

async def call_solana_rpc(method: str, params: list, timeout: int = 30, retries: int = 3, initial_delay: float = 5.0):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    headers = {"Content-Type": "application/json"}
    
    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.post(settings.SOLANA_RPC_URL, json=payload, headers=headers) as response:
                    if response.status == 429:
                        delay = initial_delay * (2 ** attempt)
                        logger.warning(f"RPC {method} hit rate limit (429). Retrying in {delay:.2f} seconds (attempt {attempt + 1}/{retries})...")
                        await asyncio.sleep(delay)
                        continue
                    
                    response.raise_for_status()
                    result = await response.json()
                    if 'error' in result:
                        logger.error(f"RPC {method} failed: {result['error']}")
                        raise HTTPException(status_code=500, detail=f"RPC Error ({result['error'].get('code', 'N/A')}): {result['error'].get('message', 'Unknown RPC error')}")
                    return result['result']
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error during RPC call {method} (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                delay = initial_delay * (2 ** attempt)
                logger.info(f"Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
            else:
                raise HTTPException(status_code=503, detail=f"Failed to connect to Solana RPC after multiple retries: {e}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout during RPC call {method} (attempt {attempt + 1}/{retries})")
            if attempt < retries - 1:
                delay = initial_delay * (2 ** attempt)
                logger.info(f"Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
            else:
                raise HTTPException(status_code=504, detail="Solana RPC call timed out after multiple retries.")
        except Exception as e:
            logger.error(f"An unexpected error occurred during RPC call {method} (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                delay = initial_delay * (2 ** attempt)
                logger.info(f"Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
            else:
                raise HTTPException(status_code=500, detail=f"An unexpected error occurred after multiple retries: {e}")
    
    raise HTTPException(status_code=500, detail=f"RPC call {method} failed after {retries} attempts.")

async def get_token_supply(token_address: str):
    try:
        mint_info = await call_solana_rpc("getAccountInfo", [
            token_address,
            {"encoding": "jsonParsed", "commitment": "confirmed"}
        ])
        
        if mint_info and mint_info.get("value") and mint_info["value"].get("data"):
            supply = mint_info["value"]["data"]["parsed"]["info"]["supply"]
            decimals = mint_info["value"]["data"]["parsed"]["info"]["decimals"]
            ui_supply = float(supply) / (10**decimals)
            return {"value": {"uiAmount": ui_supply, "decimals": decimals}}
        return None
    except Exception as e:
        logger.error(f"Error getting token supply: {e}", exc_info=True)
        return None

async def get_signatures_for_address(address: str, limit: int = 50):
    try:
        params = [address, {"limit": limit, "commitment": "confirmed"}]
        result = await call_solana_rpc("getSignaturesForAddress", params)
        return result or []
    except Exception as e:
        logger.error(f"Error getting signatures for {address}: {e}", exc_info=True)
        return None

async def get_transaction(signature: str):
    try:
        params = [signature, {"encoding": "jsonParsed", "commitment": "confirmed"}]
        result = await call_solana_rpc("getTransaction", params, timeout=20)
        return result
    except Exception as e:
        logger.error(f"Error getting transaction {signature}: {e}", exc_info=True)
        return None

async def get_account_balance(address: str):
    try:
        result = await call_solana_rpc("getBalance", [address])
        return result
    except Exception as e:
        logger.error(f"Error getting SOL balance: {e}", exc_info=True)
        return 0