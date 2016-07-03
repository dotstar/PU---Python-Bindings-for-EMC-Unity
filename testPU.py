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
    a = pu.array.array(ipaddr=host, user=user, password=password)
    lun = 'lunderdog'
    snapName = 'testSnap_{}'.format(os.getpid())  # Get a modestly unique snap Name
    snap = a.snapByName(lun, snapName)
    import time

    time.sleep(1)
    a.deleteSnap(snapName=snapName)
