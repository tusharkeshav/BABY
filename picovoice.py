import pvporcupine
from pvrecorder import PvRecorder
from get_config import get_config

SECTION = 'picovoice'

keyword_custom = ['hey baby']
keyword_default = ['picovoice', 'bumblebee', 'ok google', 'alexa']

porcupine_custom = pvporcupine.create(access_key=get_config(SECTION, 'access_key'),
                                      keyword_paths=[get_config(section=SECTION, key='custom_wake_word_path')],
                                      keywords=keyword_custom)
porcupine_default = pvporcupine.create(access_key=get_config(SECTION, 'access_key'),
                                       model_path=get_config(SECTION, 'wake_word_default_model'),
                                       keywords=keyword_default)

recoder = PvRecorder(device_index=-1, frame_length=porcupine_default.frame_length)


def detect_wake_word():
    try:
        print('*********** Starting Recording and checking for waking word ************')
        recoder.start()
        while True:
            recorded_frame = recoder.read()
            if any([porcupine_custom.process(recorded_frame) >= 0, porcupine_default.process(recorded_frame) >= 0]):
                print('word detected')
                return True

    except KeyboardInterrupt:
        recoder.stop()
    finally:
        porcupine_custom.delete()
        porcupine_default.delete()
        recoder.delete()


print(detect_wake_word())
