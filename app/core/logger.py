import os
import logging
from logging.handlers import RotatingFileHandler

# Base directory (e.g., /opt/render/project/src/app)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Logs directory path
LOG_DIR = os.path.join(BASE_DIR, "logs")

# ✅ Ensure logs directory exists (even on Render)
os.makedirs(LOG_DIR, exist_ok=True)

# Log file path
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Formatter
formatter = logging.Formatter(
    "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)

# Rotating file handler (local use only)
file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=5_000_000,
    backupCount=5,
    encoding="utf-8"
)
file_handler.setFormatter(formatter)

# Console handler (always active — useful for Render logs)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Main logger
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

# Attach handlers
logger.addHandler(console_handler)

# ✅ Only use file logging locally (Render's filesystem is temporary)
if os.getenv("RENDER", "false").lower() != "true":
    logger.addHandler(file_handler)

logger.propagate = False
