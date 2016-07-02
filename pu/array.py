#!/usr/bin/eval python
'''
PU - Python for Unity
Simple python bindings for snapshots on Unity
Draws from EMC Perl examples and EMC OpenStack driver(s) at https://github.com/emc-openstack/vnxe-cinder-driver
'''
# Turn this into a module, then turn it into something
# more object oriented.
# 2 July 2016
# Dickerson

import json
import logging
import os
import sys

import requests
from requests.auth import HTTPBasicAuth


class array(object):
    ''' class ARRAY - a storage device which we creates snaps, LUNS, and filesystems
    '''

    def __init__(self, ipaddr, user='admin', password='Password123#'):
        ''' Create an array
        :param ipaddr: ip address
        :param user: administrative login
        :param password: Password
        :return:
        '''
        # Use the session to avoid repeatedly creating TCP sessions to the array

        # Urllib is noisy about bad certificates - turn this off.
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        def _ping(ip):
            '''
            from http://stackoverflow.com/questions/2953462/pinging-servers-in-python
            :param ip: ip address
            :return: true if reachable
            '''
            import subprocess, platform
            # Ping parameters as function of OS
            ping_str = "-n 1" if platform.system().lower() == "windows" else "-c 1"
            args = "ping " + " " + ping_str + " " + ip
            need_sh = False if platform.system().lower() == "windows" else True
            # Ping
            return subprocess.call(args, shell=need_sh) == 0

        def _authenticate(urlbase, name, passw, timeout):
            logging.debug('checking authentication')
            u = urlbase + '/api/types/system/instances'  # Simple get to check login access
            try:
                r = session.get(url=u,
                                verify=False,
                                headers=headers,
                                auth=HTTPBasicAuth(user, password),
                                timeout=timeout
                                )
                cookies = r.cookies
                csrf_token = r.headers['emc-csrf-token']  # Add to headers to reduce risk of client side injection
                headers['EMC-CSRF-TOKEN'] = csrf_token

                rc = True
            except:
                e = sys.exc_info()
                logging.critical(e)
                raise
            return rc

        # Ping the ipaddr to see if it is reachable
        print('INIT CALLED')
        try:
            rc = _ping(ipaddr)
            logging.debug('ping of {} succeeded'.format(ipaddr))
        except:
            logging.fatal("can't ping array {}".format(ipaddr))
            raise

        urlbase = 'https://{}:443'.format(ipaddr)
        logging.debug('host: {} - user: {} - password: {}'.format(ipaddr, user, password))
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json',
                   'Accept_language': 'en_US',
                   'X-EMC-REST-CLIENT': 'true'
                   }
        timeout = 12
        session = requests.Session()
        if not _authenticate(urlbase, ipaddr, password, timeout):
            logging.critical("couldn't authenticate to array {}".format(ipaddr))
        cookies = session.cookies
        logging.debug('array instantiated')


def disable_urllib_warnings():
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def getSnapIdByName(snapName):
    '''

    :param snapName:
    :return:
     SnapID if the snapshot name already exists
     False if the snapshot name doesn't already exist
    '''

    global s
    global urlbase
    u = urlbase + '/api/types/snap/instances'  # All Snapshots
    returnCode = False
    ids = getIds(u)
    for snapId in ids:
        u = urlbase + '/api/instances/snap/{}?fields=name'.format(snapId)
        logging.debug(u)
        snapInstance = s.get(url=u)
        if snapInstance.ok:
            snapJson = (json.loads(snapInstance.content.decode('utf-8')))
            thisSnapName = snapJson['content']['name']
            if thisSnapName == snapName:
                returnCode = snapJson['content']['id']
                break
    return (returnCode)


def prettyJson(j):
    '''
    utility routine to print indented JSON
    :param j:
    :return:
    '''
    print(json.dumps(j, indent=2, sort_keys=True))


def getAndPrintJson(u):
    '''
    get from the REST API and print
    mostly this is for debugging and understanding the API
    :param u:
    :return:
    '''
    logging.debug(u)
    snapInstance = s.get(url=u)
    snapInstanceJson = (json.loads(snapInstance.content.decode('utf-8')))
    prettyJson(snapInstanceJson)


def getIds(url):
    '''
    convenience routine to walk a list of instances, luns, etc
    and return their IDs
    :param url:
    :return:
    '''
    idList = []
    logging.debug(url)
    ids = s.get(url)
    js = json.loads(ids.content.decode('utf-8'))
    # prettyJson(js)
    for entry in js['entries']:
        id = entry['content']['id']
        idList.append(id)
        # print ('id: {} idList: {}'.format(id,idList))
    return idList


def mapNameToStorageResourceID(name):
    instances = getIds(urlbase + '/api/types/lun/instances')
    storageResourceID = ""
    for i in instances:
        u = urlbase + '/api/instances/lun/{}?fields=name,storageResource'.format(i)
        logging.debug(u)
        lunInstance = s.get(url=u)
        if lunInstance.ok:
            lunJSON = (json.loads(lunInstance.content.decode('utf-8')))
            thisLunName = lunJSON['content']["name"]
            if thisLunName == lunName:
                # storageResourceID = lunJSON['content']['storageResource']['id']
                storageResourceID = lunJSON['content']['storageResource']
                break
    return (storageResourceID)


def lunCreateSnap(lunName, snapName):
    """

    :rtype: JSON object representing the SNAP ID - or False
    """
    returnCode = False
    # map the lunName to the storageResourceID
    storageResourceID = mapNameToStorageResourceID(lunName)
    if not storageResourceID:
        logging.warning("couldn't find a LUN named {}".format(lunName))
        return returnCode

    # make sure the snap shot doesn't already exist
    if getSnapIdByName(snapName):
        logging.warning("snapshot name {} already exists - please pick a different name".format(snapName))
        return returnCode

    # create the snap
    u = urlbase + '/api/types/snap/instances'
    storageResourceID = json.dumps(storageResourceID)
    body = '{' + '"storageResource" : {} , "name" : "{}" '.format(storageResourceID, snapName) + '}'

    r = s.post(url=u, data=body, headers=headers, verify=False)
    if r.ok:
        returnCode = json.loads(r.content.decode('utf-8'))
    return returnCode


def lunDeleteSnapByName(snapName):
    '''

    :param snapName: a string with the logical name of the snapShot
    :return: False on failure, True on success
    '''
    returnCode = False
    # Find the ID associated with Name
    snapID = getSnapIdByName(snapName)
    if snapID:
        returnCode = lunDeleteSnapByID(snapID)
    return (returnCode)


def lunDeleteSnapByID(snapID):
    '''
    Delete a SNAP shot by Snap ID
    :param snapID: A String with the snapID
    :return: False on failure, True on success
    '''
    returnCode = False
    # check input - should be a positive integer
    try:
        i = int(snapID)
        if i <= 0:
            return returnCode
    except:
        logging.warning('bad input received in lunDeleteSnapByID [{}]'.format(snapID))
        return returnCode

    u = urlbase + '/api/instances/snap/' + snapID
    r = s.delete(url=u, verify=False, headers=headers)
    if r.ok:
        returnCode = True

    return (returnCode)


if __name__ == "__main__":

    host = '192.168.23.21'
    user = 'configureme'
    password = 'Password123#'

    disable_urllib_warnings()

    logging.basicConfig(level=logging.DEBUG)
    logging.debug('host: {} - user: {} - password: {}'.format(host, user, password))
    urlbase = 'https://{}:443'.format(host)
    headers = {'Accept': 'application/json',
               'Content-Type': 'application/json',
               'Accept_language': 'en_US',
               'X-EMC-REST-CLIENT': 'true'
               }

    timeout = 12.0  # Seconds to wait for server to respond
    if not authenticate(urlbase, name=user, passw=password, timeout=timeout):
        logging.critical('Authentication Failed, exiting')
        exit(False)
    else:
        # Get a list of pools as a test
        # u = urlbase + '/api/types/loginSessionInfo/instances' # Test URL - all login info


        # Create a snapshot
        lunName = 'lunderdog'
        u = urlbase + '/api/types/snap/instances'
        requestBody = {}
        # Create n snaps
        snaps = []
        deleteSnap = False
        for i in range(0, 10):
            snapName = 'testSnap_{}_{}'.format(os.getpid(), i)
            snaps.append(snapName)
            rc = lunCreateSnap('lunderdog', snapName)
            if rc:
                logging.debug('snapshot {} success'.format(snapName))
                snapID = rc['content']['id']
                logging.debug('snap shot {} - ID = {}'.format(snapName, snapID))
                if deleteSnap:
                    # rc = lunDeleteSnapByID(snapID)
                    rc = lunDeleteSnapByName(snapName)
                    if rc:
                        logging.debug('delete of snapshot {} success'.format(snapID))
            else:
                logging.debug('snapshot {} failed'.format(snapName))

        for snapName in snaps:
            lunDeleteSnapByName(snapName)


            # What does a storageResource look like ?
            # snapId = '38654705703'
            # u = urlbase + '/api/instances/snap/{}?fields=id,name,description,lun,storageResource,size'.format(snapId)
            # Print all of the storage
            # getAndPrintJson(u)

            # getAndPrintJson(urlbase + '/api/types/lun/instances' )
            # instances = getIds(urlbase + '/api/types/lun/instances')
            # for i in instances:
            #     # For each LUN instance, print some details
            #     getAndPrintJson(urlbase +
            #                     '/api/instances/lun/{}/'.format(i) +
            #                     '?fields=id,health,name,description,type,storageResource'
            #                     )
