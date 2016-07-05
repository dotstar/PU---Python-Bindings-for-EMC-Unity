#!/usr/bin/eval python

"""
Driver program to test pu.py
"""

import logging
import os

import pu

if __name__ == "__main__":
    host = '192.168.23.21'
    user = 'configureme'
    password = 'Password123#'

    # disable_urllib_warnings()

    logging.basicConfig(level=logging.DEBUG)
    logging.debug('host: {} - user: {} - password: {}'.format(host, user, password))
    # Authenticate to array ...
    a = pu.array(ipaddr=host, user=user, password=password)

    # Get and print from array
    testUtility = True
    if testUtility:
        print(a.getSystemInformation)

    testSnap = False
    if testSnap:
        lun = 'lunderdog'
        snapName = 'testSnap_{}'.format(os.getpid())  # Get a modestly unique snap Name
        snap = a.snapByName(lun, snapName)
        print("snap returns as {}".format(snap))
        # snap.delete()
        a.deleteSnap(snapName=snapName)
