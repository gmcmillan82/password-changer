#!/usr/bin/env python

from __future__ import print_function

from __future__ import absolute_import

import pexpect
import sys, getpass
# import logging

try:
    raw_input
except NameError:
    raw_input = input


COMMAND_PROMPT = '[$#] '
TERMINAL_PROMPT = r'Terminal type\?'
TERMINAL_TYPE = 'vt100'
SSH_NEWKEY = r'Are you sure you want to continue connecting \(yes/no\)\? '
SSH_NEWKEY2 = r'Are you sure you want to continue connecting \(yes/no/\[fingerprint\]\)\? '
PASS_PROMPT1 = r'[Pp]assword:'
PASS_PROMPT2 = r'Enter your PASSWORD:'
# logging.basicConfig(level=logging.INFO, filename='commandserver.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')


def login(host, user, password):

    # Initiate ssh connection
    child = pexpect.spawn('ssh -l %s %s'%(user, host))
    response = child.expect([SSH_NEWKEY, SSH_NEWKEY2, PASS_PROMPT1, PASS_PROMPT2])

    # Check if ssh authenticity prompt appears
    if response <= 1:
        child.sendline('yes')
        response = child.expect([SSH_NEWKEY, SSH_NEWKEY2, PASS_PROMPT1, PASS_PROMPT2])

    # Attempt to login 
    try:
        child.sendline(password)
        response = child.expect(['Permission denied', TERMINAL_PROMPT, COMMAND_PROMPT])

        if response == 0:
            print('Permission denied on host:', host, "Please check your password.")
            
        if response != 0:
            child.sendline(TERMINAL_TYPE)
            child.expect(COMMAND_PROMPT)
            return child

    except pexpect.exceptions.TIMEOUT as error:
        print("Timeout exceeded on host: ", host, error)
        pass

    except pexpect.exceptions.EOF as error:
        print("Issue with EOF on host: ", host, error)
        pass

    except pexpect.ExceptionPexpect as error:
        print("Unhandled exception on host: ", host, error)
        pass


def change_password(child, user, oldpassword, newpassword):

    child.sendline('passwd')
    response = child.expect(['[Oo]ld [Pp]assword', '.current.*password', '[Nn]ew [Pp]assword', '[Nn]ew UNIX [Pp]assword'])
    # Root does not require old password, so it gets to bypass the next step.
    if response <= 1:
        child.sendline(oldpassword)
        child.expect(['[Nn]ew UNIX [Pp]assword: ', '[Nn]ew [Pp]assword: '])
    child.sendline(newpassword)

    response = child.expect(['[Nn]ew UNIX [Pp]assword: ', '[Nn]ew [Pp]assword: ', '[Rr]etype', '[Rr]e-enter'])

    if response <= 1:
        print('Host did not like new password. Here is what it said...\n', child.before, child.after)
        child.send (chr(3)) # Ctrl-C
        child.sendline('') # This should tell remote passwd command to quit.
        return
    else:
        child.sendline(newpassword)

    response = child.expect(['\r\npasswd: password updated successfully', '\r\npasswd: all authentication tokens updated successfully.'])

    if response <= 1:
        print("Password has been updated successfully")
    else:
        print("There was a problem changing your password\n", child.before, child.after)


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
                continue
            print("Changing password on: ", host)
            change_password(child, user, oldpassword, newpassword)


if __name__ == '__main__':
    main()
