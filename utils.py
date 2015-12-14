import tempfile
import subprocess
import time
import platform
import os
import binascii
import sys


ENC_PATH = '/d/.rpad_enc/'
DEC_PATH = '/home/aaron/rpad_dec/'
ENTRIES_PATH = DEC_PATH + '/entries/'


def check_mounted():
    '''
    Returns True if and only if the encfs directory is unlocked.
    Might prompt the user to unlock it.
    '''
    if os.path.ismount(DEC_PATH):
        # The encfs directory is already unlocked
        return True
    # Attempt to unlock the encfs directory
    subprocess.call(['encfs', ENC_PATH, DEC_PATH])
    return os.path.ismount(DEC_PATH)


def vim_input(visibility='Show', initial_message=''):
    assert visibility == 'Show' or visibility == 'Hide' or visibility == 'Peep'
    with tempfile.NamedTemporaryFile(suffix='.tmp') as tf:
        tf.write(initial_message)
        tf.flush()
        subprocess.call(['vim',
                         '+startinsert',
                         '-c', 'syntax match Entity /\S/ conceal cchar=*',
                         '-c', 'hi clear Conceal',
                         '-c', 'command Hide set conceallevel=1 | set concealcursor=nvic',
                         '-c', 'command Show set conceallevel=0',
                         '-c', 'command Peep set conceallevel=1 | set concealcursor=nvc',
                         '-c', 'command Help echo "Hide Show Peep"',
                         '-c', visibility,
                         tf.name])
        text = tf.read()
    return text.strip()


def time_str():
    '''
    Same format as `date` utility
    '''
    return time.strftime('%a %b %d %H:%M:%S %Z %Y')


def header(visibility):
    return time_str() + ' host=' + platform.node() + ' mode=' + visibility


def footer():
    return time_str()


def entry_filename():
    '''
    Format is current-UNIX-time-in-seconds_random-4-byte-hex-number
    '''
    return ENTRIES_PATH + '/' + str(int(time.time())) + '_' + binascii.b2a_hex(os.urandom(4))


def entry(visibility):
    if not check_mounted():
        sys.exit(1)
    filename = entry_filename()
    # Use join instead of concatenating strings because vim_input() might be large
    text = '\n'.join((header(visibility), vim_input(visibility=visibility), footer()))
    with open(filename, 'w') as f:
        f.write(text)
