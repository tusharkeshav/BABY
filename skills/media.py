from pynput.keyboard import Key, Controller, KeyCode

KEYBOARD = Controller()


def _detect_sound():
    import subprocess

    # Run the "pactl list" command and capture its output
    output = subprocess.check_output(["pactl", "list"])

    # Convert the output to a string and split it into lines
    output_str = output.decode("utf-8")
    lines = output_str.split("\n")

    # Loop through the lines and check if any streams are playing
    is_playing = False
    for line in lines:
        if "State: RUNNING" in line:
            # Audio output is detected, do something
            is_playing = True
            return True
            break

    if not is_playing:
        return False


def pause_resume_toggle():
    KEYBOARD.tap(key=Key.media_play_pause)
    pass


def resume_media():
    """
        Not working, as we are unable to figure out, how to identify if any media is running or not
        :return:
    """
    if _detect_sound() == False:
        pause_resume_toggle()
    else:
        print('Audio is already running.')


def pause_media():
    '''
    Not working, as we are unable to figure out, how to identify if any media is running or not
    :return:
    '''
    if _detect_sound():
        pause_resume_toggle()
    else:
        print('Audio is already paused')


def stop_media():
    '''
    deprecated -- Dont use.
    Note: This is not ideal way to stop audio for assistant.
    Due to this, the audio wont be able to resume. It work like hard stop. NO pause/resume work
    :return:
    '''
    KEYBOARD.tap(key=KeyCode.from_vk(269025045))


def next_media():
    KEYBOARD.tap(key=Key.media_next)


def previous_media():
    KEYBOARD.tap(key=Key.media_previous)


def mute():
    KEYBOARD.tap(key=Key.media_volume_mute)


# resume_media()

# KEYBOARD.tap(key=KeyCode.from_vk(269025045))
