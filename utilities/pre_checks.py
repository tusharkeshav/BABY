import subprocess

from utilities.train_model import detect_change, train_model
from logs.Logging import log
from config.get_config import get_config


class ModuleNotInstalled(Exception):
    pass


class KeyValueNotFound(Exception):
    pass


def run(cmd: str):
    status, output = subprocess.getstatusoutput(cmd)
    return status, output
    pass


def check_installation(module: str, name: str):
    """
    This will validate, if module is installed or not
    :param name: name of the module
    :param module: module value
    :return: True if module not installed
    """
    cmd = "which " + str(module)
    status, output = run(cmd)
    if status != 0:
        log.exception(f'{name} is not installed or not in path')
        return True
    log.debug(f'{module} is installed.')
    return False


def check_property(value: str, key: str) -> bool:
    if value is None:
        log.error(f'for key:{key}, value is not defined.')
        return True
    return False


def pre_checks():
    """
    Do precheck before launching application
    Current supported precheck:
    - Check if key-value present in congif file
    - check if the necessary modules are installed or not.
    :return:
    """
    # detect sentence file change
    if detect_change():
        log.info('Sentence file is changed. Training model again.')
        train_model()

    try:
        voice2json = get_config('default', 'voice2json')
        arecord = get_config('default', 'arecord')
        play = get_config('default', 'play')
        record_file = get_config('default', 'record_file')
        xclip = get_config('default', 'xclip')
        kde_connect = get_config('phone', 'kdeconnect')

    except Exception as e:
        log.exception('The mandatory properties are not defined in config.ini')

    #   Mandatory check: Check if property exists or not
    if any([check_property(voice2json, 'voice2json'), check_property(arecord, 'arecord'), check_property(play, 'play'),
            check_property(record_file, 'record_file')]):
        raise KeyValueNotFound('Value not found for some key/s. Check logs')

    #   Optional modules: Check if property exists or not
    if any([check_property(xclip, 'xclip'), check_property(kde_connect, 'kdeconnect')]):
        log.exception('Some modules values are not defined. Some skills might not work')

    #   Mandatory checks: check if module installed or not
    if any([check_installation(module=voice2json, name='voice2json'),
            check_installation(module=arecord, name='arecord'),
            check_installation(module=play, name='play')]):
        raise ModuleNotInstalled('Module not installed or not in path. Check logs')

    #   Optional modules: check if module installed or not
    if any([check_installation(module=xclip, name='xclip'),
            check_installation(module=kde_connect, name='kde_connect')]):
        log.exception('Some non-mandatory modules are not installed. Some skills might not work')

    return True
