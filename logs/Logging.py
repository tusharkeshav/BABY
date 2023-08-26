import logging
import os
from config.get_config import get_config

LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Application.log')

log_level_info = {'DEBUG': logging.DEBUG,
                  'INFO': logging.INFO,
                  'WARNING': logging.WARNING,
                  'ERROR': logging.ERROR,
                  }

FORMAT = "[%(asctime)s %(filename)s->%(funcName)s():%(lineno)s]%(levelname)s: %(message)s"
logging.basicConfig(filename=LOG_FILE_PATH, format=FORMAT)

log = logging.getLogger(__name__)
configured_log_level = get_config('default', 'log_level', fallback='INFO').upper()
log_level = log_level_info[configured_log_level]
log.setLevel(log_level)
