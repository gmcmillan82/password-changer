#!/usr/bin/env python

from __future__ import print_function

from __future__ import absolute_import

import pexpect
import sys, getpass

try:
    raw_input
except NameError:
    raw_input = input


COMMAND_PROMPT = '[$#] '
TERMINAL_PROMPT = r'Terminal type\?'
TERMINAL_TYPE = 'vt100'
SSH_NEWKEY = r'Are you sure you want to continue connecting \(yes/no\)\?'


def login(host, user, password):

    try:
        child = pexpect.spawn('ssh -l %s %s'%(user, host))
        fout = file ("LOG.TXT","wb")
        child.logfile_read = fout
        i = child.expect([pexpect.TIMEOUT, SSH_NEWKEY, '[Pp]assword: '])

        if i == 0: # Timeout
            print('ERROR!')
            print('SSH could not login. Here is what SSH said:')
            print(child.before, child.after)
            sys.exit (1)

        if i == 1: # SSH does not have the public key. Just accept it.
            child.sendline ('yes')
            child.expect ('[Pp]assword: ')
        child.sendline(password)

        # Now we are either at the command prompt or
        # the login process is asking for our terminal type.
        i = child.expect (['Permission denied', TERMINAL_PROMPT, COMMAND_PROMPT])

        if i == 0:
            print('Permission denied on host:', host)
            sys.exit (1)

    except pexpect.TIMEOUT:
        print("Timeout exceeded on host: ", host)
        pass

    except pexpect.exceptions.EOF:
        print("Issue with EOF on host: ", host)
        print("Output from server: ", child.before, child.after)
        pass

    if i == 1:
        child.sendline(TERMINAL_TYPE)
        child.expect(COMMAND_PROMPT)
    return child


def change_password(child, user, oldpassword, newpassword):

    child.sendline('passwd')
    i = child.expect(['[Oo]ld [Pp]assword', '.current.*password', '[Nn]ew [Pp]assword'])
    # Root does not require old password, so it gets to bypass the next step.
    if i == 0 or i == 1:
        child.sendline(oldpassword)
        child.expect('[Nn]ew UNIX [Pp]assword: ')
    child.sendline(newpassword)

    i = child.expect(['[Nn]ew UNIX [Pp]assword: ', '[Rr]etype', '[Rr]e-enter'])

    if i == 0:
        print('Host did not like new password. Here is what it said...')
        print(child.before, child.after)
        child.send (chr(3)) # Ctrl-C
        child.sendline('') # This should tell remote passwd command to quit.
        return
    child.sendline(newpassword)

    i = child.expect(['passwd: password updated successfully'])
    if i == 0:
        print("Password has been updated successfully")
    else:
        print("There was a problem changing your password")



def main():

    user = raw_input("Username: ")
    listfile = raw_input("File name: ")
    oldpassword = getpass.getpass('Old password: ')
    newpassword = getpass.getpass('New password: ')

    newpasswordconfirm = getpass.getpass('Confirm New Password: ')
    if newpassword != newpasswordconfirm:
        print('New Passwords do not match.')
        return 1

    with open(listfile, 'r') as hosts:
        for host in hosts:
            child = login(host, user, oldpassword)
            if child == None:
                print('Could not login to host:', host)
                continue
            print("Changing password on: ", host)
            change_password(child, user, oldpassword, newpassword)


if __name__ == '__main__':
    main()
