from decouple import config

class Settings:
    PROJECT_NAME: str = "Automated Futures Trading Bot"
    WEBHOOK_SECRET: str = config("WEBHOOK_SECRET", default="your_super_secret_webhook_token_here")
    
    # AMP Futures / Broker API Settings
    AMP_API_URL: str = config("AMP_API_URL", default="https://api.cqg.com/sandbox/v1")  # Using CQG as a common AMP gateway proxy
    AMP_API_KEY: str = config("AMP_API_KEY", default="your_broker_api_key_here")
    AMP_ACCOUNT_ID: str = config("AMP_ACCOUNT_ID", default="YOUR_ACCOUNT_ID")
    IS_PAPER_TRADING: bool = config("IS_PAPER_TRADING", default=True, cast=bool)

settings = Settings()
