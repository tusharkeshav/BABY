import configparser as cp

config = cp.ConfigParser()
config.optionxform = str
config.read('config.ini')


class ConfigValueNotFound:
    pass


def get_config(section, key):
    value = config.get(section, key)
    if str(value) != '':
        return value
    else:
        raise ConfigValueNotFound()
