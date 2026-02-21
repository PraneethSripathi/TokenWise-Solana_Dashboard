# seed_db.py
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
from bson import ObjectId

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'tokenwise_db')
TOKEN_CONTRACT = os.environ.get('TOKEN_CONTRACT', '9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump')

if not MONGO_URL:
    raise RuntimeError("MONGO_URL is not set in environment")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

async def seed_top_holders():
    print("Seeding sample top token holders...")

    token_decimals = 6 
    

    sample_holders_data = [
        {
            "owner": "Gg7J1t9N9pB5QxQyQzQxQyQzQxQyQzQxQyQzQxQyQz",
            "address": "Gg7J1t9N9pB5QxQyQzQxQyQzQxQyQzQxQyQzQxQyQz",
            "balance": 10000000.0,
            "ui_amount": 10000000.0,
            "percentage": 0.0, # Will be calculated later
            "decimals": token_decimals
        },
        {
            "owner": "5cWz5QxQyQzQxQyQzQxQyQzQxQyQzQxQyQzQxQyQz",
            "address": "5cWz5QxQyQzQxQyQzQxQyQzQxQyQzQxQyQzQxQyQz",
            "balance": 5000000.0,
            "ui_amount": 5000000.0,
            "percentage": 0.0,
            "decimals": token_decimals
        },
        {
            "owner": "A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0U1",
            "address": "A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0U1",
            "balance": 2500000.0,
            "ui_amount": 2500000.0,
            "percentage": 0.0,
            "decimals": token_decimals
        },
        {
            "owner": "B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0U1V2",
            "address": "B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0U1V2",
            "balance": 1200000.0,
            "ui_amount": 1200000.0,
            "percentage": 0.0,
            "decimals": token_decimals
        },
        {
            "owner": "C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0U1V2W3",
            "address": "C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0U1V2W3",
            "balance": 800000.0,
            "ui_amount": 800000.0,
            "percentage": 0.0,
            "decimals": token_decimals
        },
        {
            "owner": "D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0U1V2W3X4",
            "address": "D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0U1V2W3X4",
            "balance": 500000.0,
            "ui_amount": 500000.0,
            "percentage": 0.0,
            "decimals": token_decimals
        },
        {
            "owner": "E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0U1V2W3X4Y5",
            "address": "E5F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0U1V2W3X4Y5",
            "balance": 300000.0,
            "ui_amount": 300000.0,
            "percentage": 0.0,
            "decimals": token_decimals
        },
        {
            "owner": "F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0U1V2W3X4Y5Z6",
            "address": "F6G7H8I9J0K1L2M3N4O5P6Q7R8S9T0U1V2W3X4Y5Z6",
            "balance": 200000.0,
            "ui_amount": 200000.0,
            "percentage": 0.0,
            "decimals": token_decimals
        },
        {
            "owner": "G7H8I9J0K1L2M3N4O5P6Q7R8S9T0U1V2W3X4Y5Z6A7",
            "address": "G7H8I9J0K1L2M3N4O5P6Q7R8S9T0U1V2W3X4Y5Z6A7",
            "balance": 150000.0,
            "ui_amount": 150000.0,
            "percentage": 0.0,
            "decimals": token_decimals
        },
        {
            "owner": "H8I9J0K1L2M3N4O5P6Q7R8S9T0U1V2W3X4Y5Z6A7B8",
            "address": "H8I9J0K1L2M3N4O5P6Q7R8S9T0U1V2W3X4Y5Z6A7B8",
            "balance": 100000.0,
            "ui_amount": 100000.0,
            "percentage": 0.0,
            "decimals": token_decimals
        },
        # Add 50 more entries (total 60)
        *[
            {
                "owner": f"Wallet{i:02d}Address{'X'*(44-len(str(i)))}", # Generates unique placeholder addresses
                "address": f"Account{i:02d}Address{'Y'*(44-len(str(i)))}",
                "balance": 100000.0 - (i * 1000.0), # Decreasing balance
                "ui_amount": 100000.0 - (i * 1000.0),
                "percentage": 0.0,
                "decimals": token_decimals
            }
            for i in range(10, 60)
            
        ]
    ]
    
    for holder in sample_holders_data:
        if holder["balance"] < 1.0:
            holder["balance"] = 1.0
            holder["ui_amount"] = 1.0

    
    total_sample_balance = sum(h['balance'] for h in sample_holders_data)
    dummy_total_supply = max(total_sample_balance * 100, 25_000_000_000.0) # Ensure it's large enough

    # Update percentages based on the dummy total supply
    for holder in sample_holders_data:
        holder['percentage'] = (holder['balance'] / dummy_total_supply * 100) if dummy_total_supply else 0

    snapshot = {
        "token_address": TOKEN_CONTRACT,
        "holders": sample_holders_data,
        "total_supply": dummy_total_supply,
        "holder_count": len(sample_holders_data),
        "last_updated": datetime.utcnow()
    }

    # Insert/update the snapshot
    await db.token_holders.update_one(
        {"token_address": TOKEN_CONTRACT},
        {"$set": snapshot},
        upsert=True
    )
    print(f"Inserted/Updated {len(sample_holders_data)} sample token holders into 'token_holders' collection.")

    # Also track these wallets in the 'wallets' collection so real-time monitoring can pick them up
    for holder in sample_holders_data:
        wallet_address = holder["owner"]
        existing = await db.wallets.find_one({"address": wallet_address})
        if not existing:
            wallet_tracker = {
                "address": wallet_address,
                "tracked_since": datetime.utcnow(),
                "active": True,
                "balance": holder["balance"],
                "token_amount": holder["balance"],
                "total_buys": 0,
                "total_sells": 0
            }
            await db.wallets.insert_one(wallet_tracker)
            print(f"Tracked wallet: {wallet_address[:8]}... with {holder['balance']} tokens")
        else:
            print(f"Wallet {wallet_address[:8]}... already tracked. Updating balance.")
            await db.wallets.update_one(
                {"address": wallet_address},
                {"$set": {"balance": holder["balance"], "token_amount": holder["balance"], "last_updated": datetime.utcnow()}}
            )

    print("Seeding complete.")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_top_holders())