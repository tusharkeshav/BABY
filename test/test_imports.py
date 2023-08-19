import importlib

packages = ['pytube', 'requests', 'urllib', 'webbrowser',
            'speech_recognition', 'search_engine_parser', 'spotipy',
            'screen_brightness_control', 'PyQt5', 'wikipedia',
            'bs4', 'tkinter', 'apscheduler', 'playsound', 'plyer',
            'pvporcupine', 'pvrecorder', 'pynput',
            'cv2', 'ultralytics']

for package in packages:
    try:
        importlib.import_module(name=package)
        print(f'{package} is installed')
    except Exception as E:
        print(f'Error: {package} is not installed.')
