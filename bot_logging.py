import logging

logging.basicConfig(level=logging.INFO, filename='bot.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def log_database_update(text):
    '''
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

    file_handler = logging.FileHandler('logs.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    '''
    logging.info(text)

def log_user_info(user_id, message):
    logging.info(f'USER_{user_id}: {message}')