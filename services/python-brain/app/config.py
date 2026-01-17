import os
import logging
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()


BASE_DIR = Path(__file__).parent.parent 
DATA_DIR = BASE_DIR / "models"


DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"sqlite:///{BASE_DIR}/market_data.db"
)

TOKEN = os.getenv("T_BANK_TOKEN")

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("QuantBrain")

if not TOKEN:
    logger.warning("T_BANK_TOKEN не найден! Скачивание работать не будет.")