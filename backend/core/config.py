
import os
from pathlib import Path
from pydantic_settings import BaseSettings # Use pydantic_settings for BaseSettings
from pydantic import Field
from dotenv import load_dotenv  

# Load .env file
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

class Settings(BaseSettings):
    PROJECT_NAME: str = "TokenWise Monitor"
    PROJECT_VERSION: str = "0.1.0"
    PROJECT_DESCRIPTION: str = "Real-time Solana token transaction monitor."

    MONGO_URL: str = Field(..., env="MONGO_URL")
    DB_NAME: str = Field("tokenwise_db", env="DB_NAME")

    SOLANA_RPC_URL: str = Field(..., env="SOLANA_RPC_URL")
    SOLANA_WS_URL: str = Field(..., env="SOLANA_WS_URL")
    TOKEN_CONTRACT: str = Field("9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump", env="TOKEN_CONTRACT")

    class Config:
        case_sensitive = True
        env_file = ".env" # This specifies where to find the .env file

settings = Settings()