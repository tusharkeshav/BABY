import threading
import time


def _watch_dog(target: threading.Thread, action):
    print(f'Watchdog running... Monitoring {target.getName()}')

    while True:
        time.sleep(5)
        if not target.is_alive():
            print('Watchdog: monitor thread is not running, restarting...')
            target = action()

    pass


def watch(monitor, action, name='Worker') -> threading.Thread:
    watch_ = threading.Thread(target=_watch_dog, args=(monitor, action, name),
                              daemon=True)
    return watch_
