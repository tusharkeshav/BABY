import csv
import os.path
import subprocess
import importlib.util
import sys

from logs.Logging import log
from utilities.train_model import train_model

path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
skills = os.path.join(path, 'custom_skills/skill.csv')
sentences_file = os.path.join(path, 'sentences.ini')

section = """
[{intent}]
action = ({action})\n"""

sections = {}  # declared as global variable and contain all skill data


def run(cmd) -> tuple:
    status, output = subprocess.getstatusoutput(cmd)
    return status, output


class FileTypeError(Exception):
    pass


def add_section_to_global_sections(intent, action, sentences, file_path):
    """
    Add section to global variable section, so that it can be read later.
    :param intent:
    :param action:
    :param sentences:
    :param file_path:
    :return:
    """
    log.debug('Adding skill to section dictionary. Skill: {data}'.format(data=[intent, action, sentences, file_path]))
    section = {'action': '', 'sentences': [], 'file_path': '', 'module': '', 'file_type': ''}
    global sections

    if '::' in file_path:
        file, module = file_path.split('::')
    else:
        file = file_path
        module = ''
    if not os.path.exists(file):
        raise FileNotFoundError

    file_type = os.path.splitext(file)[1]
    if file_type not in ('.py', '.sh'):
        raise FileTypeError('File extension can only be .py or .sh. Check Skill.csv file')

    section['action'] = action
    section['sentences'] = '\n'.join(sentences.split(';'))
    section['file_path'] = file
    section['module'] = module
    section['file_type'] = file_type

    sections[intent] = section


def read_section():
    """
    This will read the skill.csv file and populate sections global dictionary.
    :return:sections
    """
    log.debug('Reading skill.csv file to dump skills to sections dict.')
    with open(skills, 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        count = 0
        for row in csvreader:
            if count == 0:
                count += 1
                continue
            add_section_to_global_sections(intent=row[0], action=row[1], sentences=row[2], file_path=row[3])
    csvfile.close()
    return sections


def check_intent_exist_csv(intent):
    if intent in sections:
        log.debug(f'Intent: "{intent}" already exist. Sections: {sections}')
        return True
    return False


def check_function_existence(file_path, function_name):
    """
    Check if the function/method exist in file or not.
    :param file_path: File which is passed in skill
    :param function_name: function/method which is being checked in file
    :return: True -> If function found in file otherwise False
    """
    module_name = 'custom_module'
    # Load the module from the file
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if hasattr(module, function_name) and callable(getattr(module, function_name)):
        log.info(f"The function '{function_name}' exists in the file.")
        return True
    else:
        log.error(f"The function '{function_name}' does not exist in the file.")
        return False


def create_section_bulk():
    """
    This will write to sentence file. It will read from the csv file(sections dict) and then write to sentence file.
    :return: None
    """
    log.debug('Writing skill section to sentence file')
    sections = read_section()
    with open(sentences_file, 'a') as file:
        # print(sections)
        for sect in sections['sections']:
            file.write(str(section.format(intent=sect['intent'], action=sect['action']) + sect['sentences']) + '\n')

    file.close()


def create_section_single(intent, action, sentences):
    """
    This will write a single section to sentence file.
    :param intent:
    :param action:
    :param sentences:
    :return: None
    """
    log.debug('Writing single section to sentence file. Data: {data}'.format(data=str(section.format(intent=intent, action=action) + sentences) + '\n'))
    with open(sentences_file, 'a') as file:
        file.write(str(section.format(intent=intent, action=action) + sentences) + '\n')
    file.close()


def write_custom_skill(intent, action, sentences, file_path):
    """
    It will:
    - write to CSV file.
    - Creation single section
    - retrain the model.
    This module is mostly used when user wanted to add SKILL from UI.
    :param intent:
    :param action:
    :param sentences:
    :param file_path:
    :return:
    """
    row = [intent, action, sentences, file_path]
    log.info(f'Creating steps to add new skill. Skill data: {row}')
    with open(skills, 'a', newline='\n') as csv_file:
        csv_write = csv.writer(csv_file).writerow(row)
        csv_file.close()
    create_section_single(intent, action, sentences.replace(';', '\n'))  # This will create single section and update the sentence file
    add_section_to_global_sections(intent=intent, action=action, sentences=sentences, file_path=file_path)   # This will update the global variable sections.
    train_model()


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


# This will set the sections' dict globally. Thus reducing the reiterating over csv file again
read_section()
