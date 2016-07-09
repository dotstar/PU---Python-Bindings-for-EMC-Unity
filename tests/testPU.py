#!/usr/bin/eval python

"""
Driver program to test Python Unity bindings
"""
import os
import sys

sys.path.insert(0, os.path.abspath('..'))

import pu.snap
import json
# from snap import snap

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
    a = pu.unityarray.unityarray(ipaddr=host, user=user, password=password)

    testLUNs = False
    if testLUNs:
        # create a LUN, look it up, delete it
        logging.info('testing getStorageDict by name')
        lname = 'test_only_cdd_{}'.format(os.getpid())
        # Create a LUN for testing
        rc = a.createLUN(name=lname, pool='flash01', size=3 * self.oneGB)  # This fails if it already exists.
        if rc:
            logging.info('SUCCESS - createLUN')
        else:
            logging.info('FAILED - createLUN')

        lun = a.getStorageDict(name=lname)
        if lun['name'] != lname:
            logging.info('FAILED - getLun() by name')
        else:
            logging.info('SUCCESS - getLun() by name')
            logging.info('testing getStorageDict by id')
            lid = lun['id']
            lun = a.getStorageDict(id=lid)
            if lun['id'] == lid and lun['name'] == lname:
                logging.info('SUCCESS - getLun() by id')
            else:
                logging.info('FAILED - getLun() by id')
        rc = a.deleteStorage(name=lname, resourceType='lun')
        if rc:
            logging.info('SUCCESS - deleteStorage')
        else:
            logging.info('FAILED - deleteStorage')

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

    testFS = True
    if testFS:
        nas = a.getNAS('nas02')
        nasID = nas['id']
        print("nasID: {}".format(nasID))
        fs = a.getFS('nfs02')
        fsID = fs['id']
        print('file system: {}'.format(fsID))
        nfs = a.getNFS('vmfs_nfs')
        # nfsID = nfs['id']
        # print('NFS Share: {}'.format(nfsID))
        # exit()

        # Create a file system
        pid = os.getpid()
        fsname = '_testfs__do_not_use_{}'.format(pid)
        fsdescr = 'a test file system {} which should be uniquely named so that we can delete it at will'.format(pid)
        fspool = 'flash01'
        fssize = 3 * a.oneGB  # 3 GB
        nasname = 'nas02'

        fsNasServer = a.getNAS(nasname)
        if fsNasServer:
            logging.info('SUCCESS - getNASByName({} {})'.format(nasID, fsNasServer))
        else:
            logging.warning('FAILED - getNASByName({} {})'.format(nasID, fsNasServer))
        for i in range(0, 3):
            # create some filesystems
            logging.basicConfig(level=logging.DEBUG)
            fsname = '_testfs__do_not_use_{}_{}'.format(pid, i)
            f = a.createFileSystem(name=fsname, pool=fspool, size=fssize, nasServer=fsNasServer, description=fsdescr)
    logging.basicConfig(level=logging.DEBUG)

    testSnap = False
    if testSnap:
        lun = 'lunderdog'
        snapName = 'testSnap_{}'.format(os.getpid())  # Get a modestly unique snap Name
        snap = a.snapByName(lun, snapName)
        print("snap returns as {}".format(snap))
        # snap.delete()
        a.deleteSnap(snapName=snapName)
