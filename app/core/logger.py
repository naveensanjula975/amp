import logging
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            # In a real setup, add FileHandler with rotation here
        ]
    )
    return logging.getLogger("trading_bot")

logger = setup_logging()
