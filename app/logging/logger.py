import logging
from pathlib import Path


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


logger = logging.getLogger("flight_price_tracker")

logger.setLevel(logging.INFO)


formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)


file_handler = logging.FileHandler(
    LOG_DIR / "app.log",
    encoding="utf-8",
)

file_handler.setFormatter(
    formatter
)


console_handler = logging.StreamHandler()

console_handler.setFormatter(
    formatter
)


logger.addHandler(
    file_handler
)

logger.addHandler(
    console_handler
)