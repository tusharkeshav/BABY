import logging
import os

LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Application.log')

FORMAT = "[%(asctime)s %(filename)s->%(funcName)s():%(lineno)s]%(levelname)s: %(message)s"
logging.basicConfig(filename=LOG_FILE_PATH, format=FORMAT,  encoding='utf-8')

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
