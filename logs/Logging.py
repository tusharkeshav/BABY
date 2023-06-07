import logging
import os

# os.chdir(os.path.dirname(os.path.abspath(__file__)))

FORMAT = "[%(asctime)s %(filename)s->%(funcName)s():%(lineno)s]%(levelname)s: %(message)s"
logging.basicConfig(filename='Application.log', format=FORMAT,  encoding='utf-8')

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
