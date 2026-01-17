# src/config.py
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(exist_ok=True)

TOKEN = os.getenv("T_BANK_TOKEN")
APP_NAME = "econophysics-research"

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(APP_NAME)


if not TOKEN:
    logger.warning("Токен T_BANK_TOKEN не найден в .env! Скачивание данных работать не будет.")