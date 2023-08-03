import os

import pvporcupine
from pvrecorder import PvRecorder
from config.get_config import get_config
from logs.Logging import log

os.chdir(os.path.dirname(os.path.abspath(__file__)))
SECTION = 'picovoice'

keyword_custom = ['hey baby']
keyword_default = ['picovoice', 'bumblebee', 'ok google', 'alexa']

porcupine_custom = pvporcupine.create(access_key=get_config(SECTION, 'access_key'),
                                      keyword_paths=[get_config(section=SECTION, key='custom_wake_word_path')],
                                      keywords=keyword_custom)
porcupine_default = pvporcupine.create(access_key=get_config(SECTION, 'access_key'),
                                       model_path=get_config(SECTION, 'wake_word_default_model'),
                                       keywords=keyword_default, sensitivities=[0.4, 0.4, 0.4, 0.4])


def detect_wake_word():
    recoder = PvRecorder(device_index=-1, frame_length=porcupine_default.frame_length)
    try:
        print('*********** Starting Recording and checking for waking word ************')
        log.debug('*********** Starting Recording and checking for waking word ************')
        recoder.start()
        while True:
            recorded_frame = recoder.read()

            detected_keyword_default = porcupine_default.process(recorded_frame)
            if detected_keyword_default >= 0:
                log.debug(f'Detected keyword is: {keyword_default[detected_keyword_default]}')
                recoder.stop()
                return True
            detected_keyword_custom = porcupine_custom.process(recorded_frame)
            if detected_keyword_custom >= 0:
                log.debug(f'Detected keyword is: {keyword_custom[detected_keyword_custom]}')
                recoder.stop()
                return True

    except KeyboardInterrupt:
        recoder.stop()
    except Exception as e:
        log.exception(f'Exception occurred while reading and analyzing. Exception: {e}')
    finally:
        recoder.delete()

