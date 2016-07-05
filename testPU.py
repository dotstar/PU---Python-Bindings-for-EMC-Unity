#!/usr/bin/eval python

"""
Driver program to test pu.py
"""

import json
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
    testUtility = False
    if testUtility:
        j = a.basicSystemInfo()
        print(json.dumps(j, indent=2, sort_keys=True))
        j = a.system()
        print(json.dumps(j, indent=2, sort_keys=True))

    testLUN = True
    if testLUN:
        p = a.listPools()
        a._prettyJson(p)
        # Check a LUN which is believed to exist ...
        lunName = 'lunderdog'
        l = a.getLUN(lunName)
        if l:
            lunID = l['content']['id']
            print('lun exists -  name: {} id: {}'.format(lunName, lunID))
        else:
            print('no such lun {}'.format(lunName))

        # now create a new LUN
        lunName = 'lun_{}'.format(os.getpid())
        pool = 'flash01'
        isThinEnabled = True
        size = 20 * 1024 * 1024 * 1024
        lun = a.createLUN(lunName, pool, size, description='my 1st LUN')
        print(lun)


    testSnap = False
    if testSnap:
        lun = 'lunderdog'
        snapName = 'testSnap_{}'.format(os.getpid())  # Get a modestly unique snap Name
        snap = a.snapByName(lun, snapName)
        print("snap returns as {}".format(snap))
        # snap.delete()
        a.deleteSnap(snapName=snapName)
