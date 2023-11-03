import logging
import datetime
from pathlib import Path

logs_dir = './bot_log'
bot_logging_dir = Path(logs_dir)
bot_logging_dir.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO, filename=f'{logs_dir}/start_bot_{datetime.datetime.now().strftime("%d_%m_%y_%H_%M_%S")}.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def log_database_update(text):
    logging.info(text)

def log_user_info(user_id, message):
    logging.info(f'USER_{user_id}: {message}')