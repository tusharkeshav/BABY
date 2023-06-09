import configparser as cp
import os
config = cp.ConfigParser()
config.optionxform = str

file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../config.ini')
config.read(file_path)


class ConfigValueNotFound(Exception):
    pass


def get_config(section, key):
    value = config.get(section, key)
    if str(value) != '':
        return value
    else:
        raise ConfigValueNotFound()
