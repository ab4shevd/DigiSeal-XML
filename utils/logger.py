import sys
import os
from loguru import logger

# Удаляем стандартный вывод
logger.remove()

# Добавляем вывод в консоль с цветом и подробностями
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG"
)

# Добавляем вывод в файл
log_file = os.path.join(os.path.expanduser("~"), ".digiseal", "digiseal.log")
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logger.add(
    log_file,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    rotation="1 MB",
    retention="7 days"
)

logger.info(f"Логирование запущено. Файл лога: {log_file}")