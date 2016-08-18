import tempfile
import subprocess
import time
import platform
import os
import binascii
import sys
import shutil


# Edit for your own setup
ENC_PATH = '/d/.rpad_enc/'
# Edit for your own setup
DEC_PATH = os.path.expanduser("~") + '/rpad_dec/'
# The name of the only host that is allowed to edit past entries with `ropen`
# Edit for your own setup
CONSISTENT_HOST = 'oxygen'

DEC_GIT_PATH = DEC_PATH + '/.git'
MERGED_RPAD_PATH = DEC_PATH + '/merged_rpad.txt'
ENTRIES_PATH = DEC_PATH + '/entries/'
OLD_ENTRIES_PATH = DEC_PATH + '/old_entries/'
# If this changes, then modify `print_password.sh`
PASSWORD_PATH = os.path.expanduser("~") + '.passwords/rpad.password'
PRINT_PASSWORD_PATH = os.path.expanduser("~") + '/Dropbox/Coding/rpad/print_password.sh'


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
    if os.path.isfile(PASSWORD_PATH):
        subprocess.call(['encfs',
                         ENC_PATH,
                         DEC_PATH,
                         '--extpass=' + PRINT_PASSWORD_PATH])
    else:
        subprocess.call(['encfs', ENC_PATH, DEC_PATH])
    return os.path.ismount(DEC_PATH)


def vim_input(visibility='Show', initial_message=''):
    assert visibility == 'Show' or visibility == 'Hide' or visibility == 'Peep'
    with tempfile.NamedTemporaryFile(suffix='.tmp.txt', delete=False) as tf:
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
        # Close and re-open the file for changes to be visible on OS X
        tf.close()
        with open(tf.name) as f:
            text = f.read()
        os.unlink(tf.name)
    return text.strip()


def connection_info():
    '''
    If this script is run over ssh, connection_info() might return something like
    'beavernet-162.caltech.edu'.
    Returns None if the script is not run remotely.
    '''
    # TODO(agf): Distinguish between the different cases when None is returned
    who_am_i = subprocess.Popen(
            ['who', 'am', 'i'], stdout=subprocess.PIPE).stdout.readline().strip()
    left_paren_index = who_am_i.find('(')
    if left_paren_index == -1:
        return None
    right_paren_index = who_am_i.find(')')
    if right_paren_index == -1 or right_paren_index < left_paren_index:
        return None
    connection = who_am_i[left_paren_index + 1:right_paren_index]
    if connection == ':0':
        return None
    return connection


def time_str():
    '''
    Same format as `date` utility
    '''
    return time.strftime('%a %b %d %H:%M:%S %Z %Y')


def header(visibility):
    head_ = time_str() + ' host=' + hostname() + ' mode=' + visibility
    connection = connection_info()
    if connection:
        head_ += ' connection=' + connection
    return head_


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
                     '[auto-msg] ' + msg])
    # TODO(agf): Return results based on whether this is successful


def view_and_maybe_edit():
    if not is_mounted():
        sys.exit(1)

    is_consistent_host = hostname() == CONSISTENT_HOST

    # Get a list of entries that are not yet appended to MERGED_RPAD_PATH
    entry_filenames = []
    for f in os.listdir(ENTRIES_PATH):
        if os.path.isfile(os.path.join(ENTRIES_PATH, f)):
            entry_filenames.append(f)

    tmp_path = tmp_merged_rpad_path()
    shutil.copy2(MERGED_RPAD_PATH, tmp_path)

    if entry_filenames:
        if is_consistent_host:
            git_commit('state before merging entries')

        # Sort entries into ascending order by time
        entry_filenames.sort(key=lambda f: int(f.split('_')[0]))

        # Append the entries to tmp_rpad
        with open(tmp_path, 'a') as tmp_rpad:
            for entry_filename in entry_filenames:
                tmp_rpad.write('\n')
                with open(os.path.join(ENTRIES_PATH, entry_filename)) as entry_file:
                    for line in entry_file:
                        tmp_rpad.write(line)
                tmp_rpad.write('\n')

        if is_consistent_host:
            shutil.copy2(tmp_path, MERGED_RPAD_PATH)
            git_commit('merged ' + str(entry_filenames))
            # Move entries into OLD_ENTRIES_PATH
            for entry_filename in entry_filenames:
                os.rename(os.path.join(ENTRIES_PATH, entry_filename),
                          os.path.join(OLD_ENTRIES_PATH, entry_filename))

    if is_consistent_host:
        subprocess.call(['vim', '+', MERGED_RPAD_PATH])
        git_commit('manual edits')
    else:
        subprocess.call(['vim', '+', '-M', tmp_path])

    os.remove(tmp_path)
