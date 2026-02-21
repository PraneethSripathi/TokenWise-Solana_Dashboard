import httpx
import os
from datetime import datetime
from backend.core.database import db  # or wherever your db connection lives

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
TOKEN_HOLDER_URL = f"https://api.helius.xyz/v1/holders?api-key={HELIUS_API_KEY}&update=true"


async def fetch_token_holders(token_address: str):
    """Fetch top 60 token holders from Helius and save them in DB."""
    if not HELIUS_API_KEY:
        raise ValueError("HELIUS_API_KEY is missing from your .env")

    url = f"{TOKEN_HOLDER_URL}?api-key={HELIUS_API_KEY}&update=true"

    payload = { "mint": token_address }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)

    if response.status_code != 200:
        raise Exception(f"Helius Error {response.status_code}: {response.text}")

    data = response.json()
    holders = data.get("holders", [])[:60]

    # Save holders in token_holders collection
    await db.token_holders.update_one(
        {"token_address": token_address},
        {
            "$set": {
                "token_address": token_address,
                "holders": holders,
                "holder_count": len(holders),
                "total_supply": data.get("total_supply"),
                "auto_tracked": True,
                "last_updated": datetime.utcnow()
            }
        },
        upsert=True
    )

    # Insert tracked wallets
    wallet_bulk = []
    for h in holders:
        wallet_bulk.append({
            "address": h["owner"],
            "active": True,
            "created_at": datetime.utcnow()
        })

    if wallet_bulk:
        await db.wallets.delete_many({})
        await db.wallets.insert_many(wallet_bulk)

    return holders
