import csv
import os.path
import subprocess
import importlib.util
import sys

from logs.Logging import log

path = os.path.dirname(os.path.abspath(__file__))
filename = os.path.join(path, 'test.csv')

section = """
[{intent}]
action = ({action})\n"""

sections = {} # declared as global variable


def run(cmd) -> list:
    status, output = subprocess.getstatusoutput(cmd)
    return status, output


class FileTypeError(Exception):
    pass


def read_section():
    with open(filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        count = 0
        global sections
        sections = {}
        for row in csvreader:
            section = {'action': '', 'sentences': [], 'file_path': '', 'module': '', 'file_type': ''}
            if count == 0:
                count += 1
                continue
            section['action'] = row[1]
            section['sentences'] = '\n'.join(row[2].split(';'))
            if '::' in row[3]:
                file, module = row[3].split('::')
                if not os.path.exists(file):
                    raise FileNotFoundError
            section['file_type'] = os.path.splitext(file)[1]
            if section['file_type'] not in ('.py', '.sh'):
                raise FileTypeError('File extension can only be .py or .sh')
            section['file_path'] = file
            section['module'] = module
            sections[row[0]] = section
    csvfile.close()
    return sections


def create_section():
    sections = read_section()
    with open(os.path.join(path, 'tmp.ini'), 'a') as file:
        # print(sections)
        for sect in sections['sections']:
            file.write(str(section.format(intent=sect['intent'], action=sect['action']) + sect['sentences']) + '\n')

    file.close()


def train_model():
    cmd = "/usr/bin/voice2json --profile en train-profile"
    status, output = run(cmd)
    if status == 0:
        print('--------------------Training logs:------------------------- \n {train_logs}'.format(
            train_train_logs=output))
        log.info('Model trained successfully')


def load_custom_skill(intent: str):
    # sections = read_section()
    log.debug('Reading custom skills. DATA: {data}'.format(data=sections))

    if intent in sections:
        print(sections[intent]['file_path'])
        file_path, module, file_type = sections[intent]['file_path'], sections[intent]['module'], sections[intent]['file_type']
        print(f'file path: {file_path}')
        print(f'module path: {module}')
        if file_type == '.py':
            spec = importlib.util.spec_from_file_location(module, file_path)
            foo = importlib.util.module_from_spec(spec)
            sys.modules[module] = foo
            spec.loader.exec_module(foo)
            function = getattr(foo, module) # This will help to trigger the function which is getting stored in string(module) and its persent in the file
            function()
        elif file_type == '.sh':
            status, output = subprocess.getstatusoutput(file_path)
            log.info(f'The command {file_path} executed. Status: {status} and Output: {output}')
    else:
        log.error('Intent: {intent} not found'.format(intent=intent))


read_section()
load_custom_skill('insult')
