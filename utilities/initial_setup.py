from subprocess import getstatusoutput
import os
from utilities.train_model import train_model
from logs.Logging import log

file_path = os.path.abspath(__file__)
folder_path = os.path.dirname(os.path.dirname(file_path))
HOME = os.environ['HOME']
linux_essential_dependencies = ['python3-tk',
                                'sox',
                                'alsa-tools',
                                'wget',
                                'espeak',
                                'jq',
                                'libstdc++6',
                                'perl',
                                'libportaudio2',
                                'libatlas3-base',
                                'libffi-dev',
                                'portaudio19-dev']

linux_optional_dependencies = ['rfkill',
                               'kdeconnect',
                               'xdotools']

install_broken_dependencies = 'sudo apt-get install -f'


def run(cmd: str, raise_error: bool = True) -> tuple:
    status, output = getstatusoutput(cmd)

    if raise_error and status != 0:
        raise Exception(f'Command: {cmd} failed with an error: {output}')
    return status, output


def install_linux_dependencies():
    cmd = 'sudo apt-get install -y {package}'
    for dependency in linux_essential_dependencies:
        log.info(f'Installing essential dependency: {dependency}')
        print(f'Installing essential dependency: {dependency}')
        run(cmd.format(package=dependency))

    for dependency in linux_optional_dependencies:
        log.info(f'Installing optional dependency: {dependency}')
        print(f'Installing optional dependency: {dependency}')
        run(cmd.format(package=dependency), raise_error=False)
    pass


def download_profile():
    log.info('Downloading Voice2json profile')
    print('Downloading Voice2json profile')
    cmd = '/usr/bin/voice2json download-profile'
    run(cmd)

    # after download delete sentence file
    log.info('Creating symlink to correct sentence file')
    print('Creating symlink to correct sentence file')
    os.remove(os.path.join(HOME, '.local/share/voice2json/en-us_kaldi-zamia/sentences.ini'))
    #
    # # create symlink to correct sentence file
    os.symlink(f'{folder_path}/sentences.ini', f'{HOME}/.local/share/voice2json/en-us_kaldi-zamia/sentences.ini')
    log.info('Training model')
    print('Training model')
    train_model()


def install_python_requirements():
    cmd = f'{folder_path}/usr/local/bin/python3 -m pip install -r {folder_path}/requirements.txt'
    run(cmd)


def install_voice2json():
    log.info('Downloading Voice2json')
    print('Downloading Voice2json')
    download_voice2json = f'cd /tmp && wget https://github.com/synesthesiam/voice2json/releases/download/v2.1' \
                          f'/voice2json_2.1_amd64.deb '
    run(cmd=download_voice2json)

    log.info('Installing Voice2json')
    print('Installing Voice2json')
    install_voice2json = 'sudo dpkg -i /tmp/voice2json_2.1_amd64.deb'
    run(cmd=install_voice2json)

    run(cmd=install_broken_dependencies)

    # Libssl and libffi binary hot fix
    try:
        log.info('Downloading and installing LibSSL')
        print('Downloading and installing LibSSL')
        lib_ssl_download = 'cd /tmp && wget http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1f' \
                           '-1ubuntu2.19_amd64.deb '
        run(cmd=lib_ssl_download)

        lib_ssl_binary_install = 'sudo dpkg -i /tmp/libssl1.1_1.1.1f-1ubuntu2.19_amd64.deb'
        run(cmd=lib_ssl_binary_install)
        run(cmd=install_broken_dependencies)

        log.info('Downloading and installing Libffi')
        print('Downloading and installing Libffi')
        libffi_binary_download = 'cd /tmp && wget http://archive.ubuntu.com/ubuntu/pool/main/libf/libffi/libffi6_3.2' \
                                 '.1-8_amd64.deb '
        libffi_binary_install = 'sudo dpkg -i /tmp/libffi6_3.2.1-8_amd64.deb'
        run(cmd=libffi_binary_download)
        run(cmd=libffi_binary_install)
        run(cmd=install_broken_dependencies)
    except Exception as e:
        log.info(f'Error while installing Libssl {e}')
        print(f'Error while installing Libssl {e}')


def initial_setup():
    install_linux_dependencies()
    install_voice2json()
    download_profile()
    install_python_requirements()
    pass


if __name__ == '__main__':
    initial_setup()
