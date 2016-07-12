#!/usr/bin/eval python

"""
Driver program to test Python Unity bindings
"""
import os
import sys

sys.path.insert(0, os.path.abspath('..'))

from pu.unityarray import unityarray

import logging


def printTestResult(result, name=""):
    if result:
        logging.info('SUCCESS - {}'.format(name))
    else:
        logging.info('FAILED - {}'.format(name))


if __name__ == "__main__":
    host = '192.168.23.21'
    user = 'configureme'
    password = 'Password123#'

    # disable_urllib_warnings() # by being at least logging.INFO

    logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        level=logging.INFO)
    logging.debug('host: {} - user: {} - password: {}'.format(host, user, password))

    # Authenticate to array ...
    a = unityarray(ipaddr=host, user=user, password=password)

    testLUNs = True
    if testLUNs:
        # create a LUN, look it up, delete it
        logging.info('testing createLUN by name')
        lname = 'test_only_cdd_{}'.format(os.getpid())
        # Create a LUN for testing
        rc = a.createLUN(name=lname, pool='flash01', size=3 * a.oneGB)  # This fails if it already exists.
        printTestResult(rc, 'createLun()')

        logging.info('testing getLUN by name')
        lun = a.getLUN(name=lname)
        printTestResult(lun, 'getLUN()')

        logging.info('testing deleteLUN for a LUN named {}'.format(lname))
        rc = a.deleteLUN(name=lname)
        printTestResult(rc, 'deleteLUN() [LUN]')

    # Get and print from array
    testUtility = True
    logging.info('testing utilities')
    if testUtility:
        j = a.basicSystemInfo()
        printTestResult(j, 'basicSystemInfo()')
        # print(json.dumps(j, indent=2, sort_keys=True))

        j = a.system()
        printTestResult(j, 'system()')
        # print(json.dumps(j, indent=2, sort_keys=True))

        j = a.getNASServers()
        printTestResult(j, 'getNASServers()')

    testFS = True
    if testFS:
        nas = a.getNAS('nas02')
        nasID = nas['id']
        printTestResult(nas, 'getNAS()')
        # print("nasID: {}".format(nasID))

        fs = a.getFS('nfs02')
        fsID = fs['id']
        # print('file system: {}'.format(fsID))
        printTestResult(fs, 'getFS()')

        # nfs = a.getNFS('vmfs_nfs')
        # nfsID = nfs['id']
        # print('NFS Share: {}'.format(nfsID))
        # exit()

        # Create a file system
        logging.info('test: create a filesystem ...')
        pid = os.getpid()
        fsname = '_testfs__do_not_use_{}'.format(pid)
        fsdescr = 'a test file system {} which should be uniquely named so that we can delete it at will'.format(pid)
        fspool = 'flash01'
        fssize = 3 * a.oneGB  # 3 GB
        nasname = 'nas02'

        fsNasServer = a.getNAS(nasname)
        printTestResult(fsNasServer, 'getNAS()')

        for i in range(0, 1):
            # create some filesystems
            logging.basicConfig(level=logging.DEBUG)
            fsname = '_testfs__do_not_use_{}_{}'.format(pid, i)
            logging.info('calling createFS({}) -- this takes a minute ...'.format(fsname))
            f = a.createFileSystem(name=fsname, pool=fspool, size=fssize, nasServer=fsNasServer, description=fsdescr)
            printTestResult(f, 'createFileSystem()')
            if f:
                # If we successfully created the temporary file system, delete it.
                logging.info('calling deleteFS({}) -- this takes 15+ seconds ...'.format(fsname))
                rc = a.deleteFS(fsname)
                printTestResult(rc, fsname)

    testSnap = True
    if testSnap:
        # Create a LUN
        # Snap shot the LUN x 2
        # Delete one Snap
        # Delete the LUN and take the remaining snap with it.
        lname = '_cdd_test_lun_{}'.format(os.getpid())
        pool = 'flash01'
        size = 4 * a.oneGB
        rc = a.createLUN(name=lname, pool=pool, size=size)  # This fails if it already exists.
        printTestResult(rc, 'createLUN()')
        if not rc:
            logging.critical("FAILED - couldn't create LUN {} in pool {}".format(lname, pool))
        else:
            snapName = 'testSnap_{}_1'.format(os.getpid())  # Get a modestly unique snap Name
            snap = a.createsnap(lname, snapName)
            printTestResult(snap, 'createSnap({})'.format(snapName))

            snapName = 'testSnap_{}_2'.format(os.getpid())  # Get a modestly unique snap Name
            snap = a.createsnap(lname, snapName)
            printTestResult(snap, 'createSnap({})'.format(snapName))

            # Delete the most recently created Snap
            rc = a.deleteSnap(snapName=snapName)
            printTestResult(rc, 'deleteSnap({})'.format(snapName))
            # Now delete the LUN
            rc = a.deleteStorage(name=lname)
            printTestResult(rc, 'deleteStorage({})'.format(lname))

    logging.info('All tests complete')
