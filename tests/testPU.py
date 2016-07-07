#!/usr/bin/eval python

"""
Driver program to test pu.py
"""


import os
import sys
sys.path.insert(0, os.path.abspath('..'))
from pu import array
import json
import logging

if __name__ == "__main__":
    host = '192.168.23.21'
    user = 'configureme'
    password = 'Password123#'

    # disable_urllib_warnings() # by being at least logging.INFO

    logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        level=logging.DEBUG)
    logging.debug('host: {} - user: {} - password: {}'.format(host, user, password))
    # Authenticate to array ...
    a = array(ipaddr=host, user=user, password=password)

    # Get and print from array
    testUtility = False
    if testUtility:
        j = a.basicSystemInfo()
        print(json.dumps(j, indent=2, sort_keys=True))
        j = a.system()
        print(json.dumps(j, indent=2, sort_keys=True))
        j = a.getNASServers()
        if j:
            print(json.dumps(j, indent=2, sort_keys=True))

    nasID = a.getNASIdFromName('nas02')
    print ("nasID: {}".format(nasID))
    exit()

    testFS = False
    if testFS:
        f = a.createFS()
        exit()

    testLUN = True
    if testLUN:
        p = a.listPools()
        # a._prettyJson(p)
        # Check a LUN which is believed to exist ...
        lunName = 'lunderdog'
        l = a.getLUN(name=lunName)
        # a._prettyJson(l)
        if l:
            lunID = l['content']['id']
            logging.info('SUCCESS - lun exists -  name: {} id: {}'.format(lunName, lunID))
        else:
            logging.info('TEST FAILED - no such lun {}'.format(lunName))

        # now create some new LUNs
        lunName = 'lun_{}'.format(os.getpid())
        pool = 'flash01'
        isThinEnabled = True
        # Create some LUNs, then Delete them
        oneGB = 1 * 1024 * 1024 * 1024
        lunsCreated = []
        nluns = 4
        logging.info('creating {} LUNs'.format(nluns))
        for i in range(0, nluns):
            size = oneGB
            name = "{}_{}".format(lunName, i)
            lun = a.createLUN(name, pool, size, description='my LUN description')
            lunsCreated.append(lun)
            logging.info("lun {} create with status: {}".format(name, lun))

        logging.info('now deleting the same LUNs')
        # Now delete them
        for lunID in lunsCreated:
            status = a.deleteLUN(lunID=lunID)
            if status:
                logging.info('LUN {} deleted'.format(lunID))
            else:
                logging.warning('LUN deleted failed for lunID {}'.format(lunID))

    testSnap = False
    if testSnap:
        lun = 'lunderdog'
        snapName = 'testSnap_{}'.format(os.getpid())  # Get a modestly unique snap Name
        snap = a.snapByName(lun, snapName)
        print("snap returns as {}".format(snap))
        # snap.delete()
        a.deleteSnap(snapName=snapName)
