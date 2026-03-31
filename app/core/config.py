from decouple import config

class Settings:
    PROJECT_NAME: str = "Automated Futures Trading Bot"
    WEBHOOK_SECRET: str = config("WEBHOOK_SECRET", default="your_super_secret_webhook_token_here")

settings = Settings()
