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
            u = self.urlbase + '/api/types/system/instances'  # Simple get to check login access
            try:
                r = self.session.get(url=u,
                                     verify=False,
                                     headers=self.headers,
                                     auth=HTTPBasicAuth(user, password),
                                     timeout=self.timeout
                                     )
                cookies = r.cookies
                csrf_token = r.headers['emc-csrf-token']  # Add to headers to reduce risk of client side injection
                self.headers['EMC-CSRF-TOKEN'] = csrf_token
                self.cookies = self.session.cookies
                rc = True
            except:
                e = sys.exc_info()
                logging.critical(e)
                raise
            return rc

        # Ping the ipaddr to see if it is reachable
        try:
            rc = _ping(ipaddr)
            logging.debug('ping of {} succeeded'.format(ipaddr))
        except:
            logging.fatal("can't ping array {}".format(ipaddr))
            raise

        self.urlbase = 'https://{}:443'.format(ipaddr)
        logging.debug('host: {} - user: {} - password: {}'.format(ipaddr, user, password))
        self.headers = {'Accept': 'application/json',
                        '.Content-Type': 'application/json',
                   'Accept_language': 'en_US',
                   'X-EMC-REST-CLIENT': 'true'
                        }
        self.timeout = 12
        self.session = requests.Session()
        self.user = user
        self.password = password
        self.ipaddr = ipaddr
        self.snapName = ""
        self.snapID = ""
        if not _authenticate(self.urlbase, self.ipaddr, self.password, self.timeout):
            logging.critical("couldn't authenticate to array {}".format(ipaddr))

        logging.debug('array instantiated')

    def _getSnapIdByName(self, snapName):
        '''

        :param snapName:
        :return:
         SnapID if the snapshot name already exists
         False if the snapshot name doesn't already exist
        '''

        u = self.urlbase + '/api/types/snap/instances'  # All Snapshots
        returnCode = False
        ids = self._getIds(u)
        for snapId in ids:
            u = self.urlbase + '/api/instances/snap/{}?fields=name'.format(snapId)
            logging.debug(u)
            snapInstance = self.session.get(url=u)
            if snapInstance.ok:
                snapJson = (json.loads(snapInstance.content.decode('utf-8')))
                thisSnapName = snapJson['content']['name']
                if thisSnapName == snapName:
                    returnCode = snapJson['content']['id']
                    break
        return (returnCode)

    def _prettyJson(self, j):
        '''
        utility routine to print indented JSON
        :param j:
        :return:
        '''
        print(json.dumps(j, indent=2, sort_keys=True))

    def _getAndPrintJson(self, u):
        '''
        get from the REST API and print
        mostly this is for debugging and understanding the API
        :param u:
        :return:
        '''
        logging.debug(u)
        instance = self.session.get(url=u)
        instanceJson = (json.loads(instance.content.decode('utf-8')))
        self._prettyJson(instanceJson)

    def _getIds(self, url):
        '''
        convenience routine to walk a list of instances, luns, etc
        and return their IDs
        :param url:
        :return:
        '''
        idList = []
        logging.debug(url)
        ids = self.session.get(url)
        js = json.loads(ids.content.decode('utf-8'))
        # prettyJson(js)
        for entry in js['entries']:
            id = entry['content']['id']
            idList.append(id)
            # print ('id: {} idList: {}'.format(id,idList))
        return idList

    def _mapNameToStorageResourceID(self, lunName):
        instances = self._getIds(self.urlbase + '/api/types/lun/instances')
        storageResourceID = ""
        for i in instances:
            u = self.urlbase + '/api/instances/lun/{}?fields=name,storageResource'.format(i)
            logging.debug(u)
            lunInstance = self.session.get(url=u)
            if lunInstance.ok:
                lunJSON = (json.loads(lunInstance.content.decode('utf-8')))
                thisLunName = lunJSON['content']["name"]
                if thisLunName == lunName:
                    # storageResourceID = lunJSON['content']['storageResource']['id']
                    storageResourceID = lunJSON['content']['storageResource']
                    break
        return (storageResourceID)

    def snapByName(self, lunName, snapName):
        """

        :rtype: JSON object representing the SNAP ID - or False
        """
        returnCode = False
        # map the lunName to the storageResourceID
        storageResourceID = self._mapNameToStorageResourceID(lunName)
        if not storageResourceID:
            logging.warning("couldn't find a LUN named {}".format(lunName))
            return returnCode

        # make sure the snap shot doesn't already exist
        if self._getSnapIdByName(snapName):
            logging.warning("snapshot name {} already exists - please pick a different name".format(snapName))
            return returnCode

        # create the snap
        u = self.urlbase + '/api/types/snap/instances'
        storageResourceID = json.dumps(storageResourceID)
        body = '{' + '"storageResource" : {} , "name" : "{}" '.format(storageResourceID, snapName) + '}'

        r = self.session.post(url=u, data=body, headers=self.headers, verify=False)
        if r.ok:
            returnCode = json.loads(r.content.decode('utf-8'))
        return returnCode

    def deleteSnap(self, snapName='', snapID=''):
        '''

        :param snapName: a string with the logical name of the snapShot
        :return: False on failure, True on success
        '''
        returnCode = False
        if not snapName and not snapID:
            print('need to provide either snapName or snapID')
            return returnCode
        if not snapID:
            # If we were provided a name, and not iD find the ID
            # If we received both, ID over-rides name
            snapID = self._getSnapIdByName(snapName)
        if snapID:
            returnCode = self._deleteSnapByID(snapID)
        return (returnCode)

    def _deleteSnapByID(self, snapID):
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
        u = self.urlbase + '/api/instances/snap/' + snapID
        r = self.session.delete(url=u, verify=False, headers=self.headers)
        if r.ok:
            returnCode = True
        return (returnCode)
