from subprocess import getstatusoutput
import os
from utilities.train_model import train_model
from logs.Logging import log

file_path = os.path.abspath(__file__)
HOME = os.environ['HOME']
linux_essential_dependencies = ['python3-tk',
                                'sox',
                                'alsa-tools']

linux_optional_dependencies = ['rfkill',
                               'kdeconnect',
                               'xdotools']


def run(cmd: str, raise_error: bool = True) -> tuple:
    status, output = getstatusoutput(cmd)

    if raise_error and status != 0:
        raise Exception(f'Command: {cmd} failed with an error: {output}')
    return status, output


def install_linux_dependencies():
    cmd = 'sudo apt install -y {package}'
    for dependency in linux_essential_dependencies:
        log.info(f'Installing essential dependency: {dependency}')
        run(cmd.format(package=dependency))

    for dependency in linux_optional_dependencies:
        log.info(f'Installing optional dependency: {dependency}')
        run(cmd.format(package=dependency), raise_error=False)
    pass


def download_profile():
    cmd = '/usr/bin/voice2json --profile en-us_kaldi-zamia download-profile'
    run(cmd)

    # after download delete sentence file
    os.remove(os.path.join(HOME, '.local/share/voice2json/en-us_kaldi-zamia/sentences.ini'))

    # create symlink to correct sentence file
    os.symlink(f'{file_path}/sentences.ini', f'{HOME}/.local/share/voice2json/en-us_kaldi-zamia/sentences.ini')
    train_model()


def install_python_requirements():
    cmd = f'{file_path}/venv/bin/python -m pip install -r {file_path}/requirement.txt'
    run(cmd)


def main():
    install_linux_dependencies()
    download_profile()
    install_python_requirements()
    pass


if __name__ == '__main__':
    main()
