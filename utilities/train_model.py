import subprocess
from logs.Logging import log


def run(cmd) -> list:
    status, output = subprocess.getstatusoutput(cmd)
    return status, output


def train_model():
    cmd = "/usr/bin/voice2json --profile en train-profile"
    status, output = run(cmd)
    if status == 0:
        log.info('Model trained successfully')
    log.debug('Model Training logs: {train_logs}'.format(train_logs=output))
