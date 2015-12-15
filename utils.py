import tempfile
import subprocess
import time
import platform
import os
import binascii
import sys
import shutil


ENC_PATH = '/d/.rpad_enc/'
DEC_PATH = '/home/aaron/rpad_dec/'
DEC_GIT_PATH = DEC_PATH + '/.git'
MERGED_RPAD_PATH = DEC_PATH + '/merged_rpad.txt'
ENTRIES_PATH = DEC_PATH + '/entries/'
OLD_ENTRIES_PATH = DEC_PATH + '/old_entries/'


def hostname():
    return platform.node()


def tmp_merged_rpad_path():
    return MERGED_RPAD_PATH + '.' + hostname() + '.tmp.txt'


def is_mounted():
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
    with tempfile.NamedTemporaryFile(suffix='.tmp.txt') as tf:
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
    return time_str() + ' host=' + hostname() + ' mode=' + visibility


def footer():
    return time_str()


def entry_filename():
    '''
    Format is current-UNIX-time-in-seconds_random-4-byte-hex-number
    '''
    return ENTRIES_PATH + '/' + str(int(time.time())) + '_' + binascii.b2a_hex(os.urandom(4))


def entry(visibility):
    if not is_mounted():
        sys.exit(1)
    filename = entry_filename()
    header_ = header(visibility)
    body = vim_input(visibility=visibility)
    if not body:
        return
    footer_ = footer()
    text = '\n'.join((header_, body, footer_))
    with open(filename, 'w') as f:
        f.write(text)


def git_commit(msg):
    subprocess.call(['git',
                     '-C', DEC_PATH,
                     'commit',
                     '-am',
                     msg])
    # TODO(agf): Return results based on whether this is successful

def merge():
    # TODO(agf): Should check that merged_rpad.txt isn't currently open in Vim
    # TODO(agf): This should only be called on one device

    # Get a list of entries to append to MERGED_RPAD_PATH
    entry_filenames = []
    for f in os.listdir(ENTRIES_PATH):
        if os.path.isfile(os.path.join(ENTRIES_PATH, f)):
            entry_filenames.append(f)
    if not entry_filenames:
        return

    git_commit('state before merging entries')

    # Sort entries into ascending order by time
    entry_filenames.sort(key=lambda f: int(f.split('_')[0]))

    # Append the entries to MERGED_RPAD_PATH
    tmp_path = tmp_merged_rpad_path()
    shutil.copy2(MERGED_RPAD_PATH, tmp_path)
    with open(tmp_path, 'a') as tmp_rpad:
        for entry_filename in entry_filenames:
            tmp_rpad.write('\n\n')
            with open(os.path.join(ENTRIES_PATH, entry_filename)) as entry_file:
                for line in entry_file:
                    tmp_rpad.write(line)
    shutil.copy2(tmp_path, MERGED_RPAD_PATH)
    os.remove(tmp_path)

    # Move entries into OLD_ENTRIES_PATH
    for entry_filename in entry_filenames:
        os.rename(os.path.join(ENTRIES_PATH, entry_filename),
                  os.path.join(OLD_ENTRIES_PATH, entry_filename))

    git_commit('merged ' + str(entry_filenames))
