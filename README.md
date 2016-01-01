*A diary application that you can use on multiple machines without having your data clobbered by Dropbox consistency issues.*

Note: At present, this is very specialized to my toolset. It has been tested on Ubuntu 14.04 and 15.10. It uses Vim 7.3 or higher for text editing, EncFS for encryption, and Git for version control. It is intended for use with Dropbox or other continuous-sync services.

**Features**
- Add entries from any machine
- Add entries with our without the text appearing on screen as you type
- View all synced entries as a single document
- Edit any number of synced entries in a version-controlled document, but only from a specially designated machine
- You can add, view, and edit entries without an active internet connection
- Everything is encrypted and protected from Dropbox consistency issues

**Setup**

Suppose that you have two machines with hostnames ALPHA and BETA, and you want ALPHA to be the specially designated machine that can edit past entries. Do the following on both machines.
```
# Install Vim
sudo apt-get install vim-gnome
# Check that Vim is version 7.3 or higher and includes the "conceal" feature
vim --version
# Install Git
sudo apt-get install git
# Install encfs
sudo apt-get install encfs
# Set up encrypted virtual filesystems. 
encfs /YOUR_PATH/Dropbox/.rpad_enc /YOUR_PATH/rpad_dec
```
Then, do the following on one of the machines and wait for the results to sync to both machines:
```
cd /YOUR_PATH/rpad_dec
mkdir entries
mkdir old_entries
touch merged_rpad.txt
git init
git add merged_rpad.txt
git commit -am "Initial, manual commit"
echo "entries/*" >> .gitignore
echo "old_entries/*" >> .gitignore
echo ".Trash/*" >> .gitignore
echo "*.tmp.txt" >> .gitignore
```
Then, do the following on both machines:
```
git clone https://github.com/AGFeldman/rpad.git /YOUR_PATH
# Edit the following variables in /YOUR_PATH/rpad/utils.py:
# ENC_PATH = /YOUR_PATH/Dropbox/.rpad_enc
# DEC_PATH = /YOUR_PATH/rpad_dec
# CONSISTENT_HOST = 'ALPHA'
# (Done editing variables)
# Suggested aliases:
echo 'alias rs="python2 /YOUR_PATH/rpad/entry_show.py"' >> ~/.bash_aliases
echo 'alias rh="python2 /YOUR_PATH/rpad/entry_hid.py"' >> ~/.bash_aliases
echo 'alias ropen="python2 /YOUR_PATH/rpad/view_and_maybe_edit.py"' >> ~/.bash_aliases
```

Now, to add an entry with text appearing on screen as you type, open a terminal and execute `rs`. To add an entry without text appearing on screen, execute `rh`. While writing an entry, try the Vim commands `Hide`, `Show`, and `Peep` to change the level of text visibility, and try the `Help` to list these additional commands.

To view all synced entries from BETA, execute `ropen`. You will not be able to edit any of the entries from BETA. To view and optionally edit synced entries from ALPHA, use the same `ropen` command. If you want to edit entries from BETA, ssh into ALPHA and use `ropen`.
