import logging
logging.basicConfig(level=logging.INFO)


def log_user_info(user_id, message):
    logging.info(f'USER_{user_id}: {message}')