import logging
import sys

logger = logging.getLogger('app_logger')
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s', datefmt='%d-%m-%Y %H:%M:%S'
)
stream_handler.setFormatter(formatter)

logger.addHandler(stream_handler)