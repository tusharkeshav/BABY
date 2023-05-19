import logging

FORMAT = "[%(asctime)s %(filename)s->%(funcName)s():%(lineno)s]%(levelname)s: %(message)s"
logging.basicConfig(filename='logs/Application.log', format=FORMAT,  encoding='utf-8')

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
