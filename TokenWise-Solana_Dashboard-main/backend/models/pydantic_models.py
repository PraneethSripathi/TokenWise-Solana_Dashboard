
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime
from bson import ObjectId # Used for default_factory with ObjectId

class TokenHolder(BaseModel):
    owner: str
    address: str
    balance: float
    ui_amount: float
    percentage: Optional[float] = None
    decimals: int = 0

class RealtimeTransaction(BaseModel):
    id: Optional[str] = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    signature: str
    timestamp: datetime
    wallet: str
    token_address: str
    amount: float
    action_type: str
    protocol: str
    block_time: int
    slot: int
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    pre_balance: Optional[float] = None
    post_balance: Optional[float] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class WalletTracker(BaseModel):
    id: Optional[str] = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    address: str
    tracked_since: datetime = Field(default_factory=datetime.utcnow)
    active: bool = True
    balance: Optional[float] = None
    token_amount: Optional[float] = None
    last_transaction: Optional[datetime] = None
    total_buys: int = 0
    total_sells: int = 0
    profit_loss: Optional[float] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        # json_encoders are handled globally

class TokenHolderSnapshot(BaseModel):
    id: Optional[str] = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    token_address: str
    holders: List[TokenHolder]
    total_supply: float
    holder_count: int
    last_updated: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        # json_encoders are handled globally

class WalletCreate(BaseModel):
    address: str