import configparser as cp
import os
config = cp.ConfigParser()
config.optionxform = str

file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../config.ini')
config.read(file_path)


class ConfigValueNotFound(Exception):
    pass


def get_config(section, key, fallback=None):
    value = config.get(section, key, fallback=fallback)
    if str(value) != '':
        return value
    else:
        return None
