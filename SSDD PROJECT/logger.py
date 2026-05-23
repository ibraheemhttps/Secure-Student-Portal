import logging

# Create logger
logger = logging.getLogger('portal')
logger.setLevel(logging.INFO)

# Log to a file called portal.log
handler = logging.FileHandler('portal.log')
handler.setLevel(logging.INFO)

# Format: time - level - message
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)