from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database and Authentication Settings
    DATABASE_URL: str
    SECRET_KEY: str

    # Paymob Settings
    PAYMOB_API_KEY: str
    PAYMOB_CARD_INTEGRATION_ID: int
    PAYMOB_WALLET_INTEGRATION_ID: int
    PAYMOB_HMAC_SECRET: str

    class Config:
        env_file = ".env"
        # Tell Pydantic to ignore any extra variables in the .env file
        extra = "ignore"

# Create a global instance of the settings to be used across the app
settings = Settings()