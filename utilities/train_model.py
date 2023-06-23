import os
import subprocess
from logs.Logging import log
from config.get_config import get_config

VOICE2JSON = get_config('default', 'voice2json')
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(cmd) -> list:
    status, output = subprocess.getstatusoutput(cmd)
    return status, output


def detect_change() -> bool:
    """
    It will detect the change in sentence file.
    :return: True if the changes are detected
    """
    sentence_path = os.path.join(path, 'sentences.ini')
    tmp_sentence_path = os.path.join(path, 'utilities/.sentence')
    recent_modified_time = str(int(os.stat(sentence_path).st_mtime))
    with open(tmp_sentence_path, 'r+') as file:
        last_modified_time = file.readline()
        if last_modified_time == recent_modified_time:
            file.close()
            return False
        else:
            file.seek(0)
            file.writelines(recent_modified_time)
            file.close()
            return True


def train_model():
    cmd = f"{VOICE2JSON} --profile en train-profile"
    status, output = run(cmd)
    if status == 0:
        log.info('Model trained successfully')
    log.debug('Model Training logs: {train_logs}'.format(train_logs=output))
