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
import os

sys.path.insert(0, os.path.abspath('.'))
from pu.unityEnums import *
import requests
from requests.auth import HTTPBasicAuth


class unityarray:
    ''' class unityarray - a storage device which we creates snaps, LUNS, and filesystems
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
                if not r.ok:
                    self._printError("GET", r)
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
        self.oneGB = 1 * 1024 * 1024 * 1024
        self.threeGB = 3 * self.oneGB
        if not _authenticate(self.urlbase, self.ipaddr, self.password, self.timeout):
            logging.critical("couldn't authenticate to array {}".format(ipaddr))

        logging.info('array instantiated')


    def _prettyJson(self, j):
        '''
        utility routine to print indented JSON
        :param j:
        :return:
        '''
        print(json.dumps(j, indent=2, sort_keys=True))

    def _getJSON(self, u):
        r = self.session.get(url=u)
        if r.ok:
            # return (json.loads(r.content.decode('utf-8')))
            return r.json()
        else:
            self._printError("GET", r)
            return False

    def _getAndPrintJson(self, u):
        '''
        get from the REST API and print
        mostly this is for debugging and understanding the API
        :param u:
        :return:
        '''
        logging.debug(u)
        instance = self._getJSON(u)
        if instance:
            self._prettyJson(instance)

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
        if not ids.ok:
            self._printError("GET", ids)
        # js = json.loads(ids.content.decode('utf-8'))
        js = ids.json()
        # prettyJson(js)
        for entry in js['entries']:
            id = entry['content']['id']
            idList.append(id)
            # print ('id: {} idList: {}'.format(id,idList))
        return idList


    def _restToJSON(self, url):
        """ Utility code used for the numerous get requests which take a REST value and traslate to JSON"""
        returnValue = False
        logging.debug(url)
        instance = self.session.get(url=url)
        if instance.ok:
            # returnValue = (json.loads(instance.content.decode('utf-8')))['content']
            returnValue = instance.json()['content']
        else:
            self._printError("GET", instance)
        return returnValue

    def basicSystemInfo(self):
        """
        :return: string with systemInformation Fields

        """
        fields = "id,model,name,softwareVersion,apiVersion,earliestApiVersion"
        url = self.urlbase + '/api/instances/basicSystemInfo/0' + '?fields=' + fields
        return (self._restToJSON(url))

    def system(self):
        """ system"""
        fields = "id,health,name,model,serialNumber,internalModel,platform,macAddress,isEULAAccepted,isUpgradeComplete,isAutoFailbackEnabled,currentPower,avgPower"
        fields = "id,health,name,model,serialNumber,internalModel,platform,macAddress,isEULAAccepted"
        fields = fields + ",isUpgradeComplete"
        # There are a couple of additional fields which apparently do not work with virtualized Unity:
        # isAutoFailbackEnabled, currentPower, avgPower
        url = self.urlbase + '/api/instances/system/0' + '?fields=' + fields
        logging.debug(url)
        return self._restToJSON(url)

    def createsnap(self, storageResourceName,
                   snapName,
                   description="",
                   isAutoDelete=False,
                   isReadOnly=False,
                   filesystemAccessType=2):
                   # filesystemAccessType=FilesystemSnapAccessTypeEnum.protocol):
        '''

        :param storageResourceName: string with the name of the file system or lun (source)
        :param snapName:  string with the name of the resulting snapshot
        :param description:
        :param isAutoDelete: Boolean
        :param isReadOnly: Boolean
        :param filesystemAccessType: protocol or checkpoint
        :return: string with snap id or False
        '''

        # map the storageResourceName to the storageResourceID
        sr = self.getStorageResource(storageResourceName)
        if not sr:
            logging.critical("couldn't associate {} with a storage resource".format(storageResourceName))
            return False  # Throw?
        # Make sure there isn't already a snap with this name
        snap = self.getSnap(snapName)
        if snap:
            logging.warning("snapshot name {} already exists - please pick a different name".format(snapName))
            return False

        # create the snap
        srbody = {}
        srbody['id'] = sr['id']
        srbody['name'] = sr['name']
        body = {}
        body['storageResource'] = srbody
        body['name'] = snapName
        body['description'] = description
        body['isAutoDelete'] = isAutoDelete
        body['isReadOnly'] = isReadOnly
        body['filesystemAccessType'] = filesystemAccessType
        jsonBody = json.dumps(body)

        # Build the URL and POST to create the Snapshot
        u = self.urlbase + '/api/types/snap/instances'
        r = self.session.post(url=u, data=jsonBody, headers=self.headers, verify=False)
        if r.ok:
            tmpDict = r.json()
            id = tmpDict['content']['id']
            logging.info("Created Snap {} on Storage Resource {} SnapID {}".format(snapName, storageResourceName,id))
            returnCode = id
        else:
            logging.info("Snapshot failed -  Snap {} on LUN {}".format(snapName, storageResourceName))
            returnCode = False
        return returnCode

    def deleteSnap(self, snapName='', snapID=''):
        '''

        :param snapName: a string with the logical name of the snapShot
        :return: False on failure, True on success
        '''
        logging.info("deleteSnap {} {}".format(snapName, snapID))
        returnCode = False
        if not snapName and not snapID:
            print('need to provide either snapName or snapID')
            return returnCode
        if not snapID:
            # If we don't have a snapID, get one
            # [ method called by name ]
            snap = self.getSnap(snapName)
            if not snap:
                logging.critical('')
                return False
            snapID = snap['id']
        if snapID:
            u = self.urlbase + '/api/instances/snap/' + snapID
            r = self.session.delete(url=u, verify=False, headers=self.headers)
            if r.ok:
                logging.info("Deleted Snap {} SnapID {}".format(snapName, snapID))
                returnCode = True
            else:
                logging.warning("Delete Failed: Snap {} SnapID {}".format(snapName, snapID))
        return (returnCode)

    def listPools(self):
        ''' list all existing pools'''
        returnCode = False
        logging.debug('method listPools')
        u = self.urlbase + '/api/types/pool/instances'
        instances = self._getIds(url=u)
        for i in instances:
            fields = 'id,health,name,description,storageResourceType,raidType,sizeFree,sizeTotal,sizeUsed,\
                    sizeSubscribed,alertThreshold,isFASTCacheEnabled,tiers,creationTime,isEmpty,poolFastVP,\
                    isHarvestEnabled,harvestState,isSnapHarvestEnabled,poolSpaceHarvestHighThreshold,\
                    poolSpaceHarvestLowThreshold,snapSpaceHarvestHighThreshold, snapSpaceHarvestLowThreshold,\
                    metadataSizeSubscribed,snapSizeSubscribed,metadataSizeUsed,snapSizeUsed,\
                    rebalanceProgress'

            u = self.urlbase + '/api/instances/pool/{}'.format(i) + '?fields=' + fields
        j = self._getJSON(u)
        if j:
            returnCode = j
        return returnCode

    def _printError(self, verb, response):
        errorText = ""
        errorCode = response.status_code
        msgs = json.loads(response.text)['error']['messages']
        for m in msgs:
            errorText = errorText + m['en-US']
        logging.warning(
            '{} failed with status {} details: {}'.format(verb, errorCode, errorText))

    def createLUN(self, name, pool, size=(3 * 1024 * 1024 * 1024), description="", lunParameters="",
                  isThinEnabled=True, fastVPParameters="",
                  defaultNode="", hostAccess="", ioLimitParameters=""):
        ''' Build new LUN'''

        returnCode = False

        logging.debug('createLun({} {},...)'.format(name, description))

        if not name:
            logging.critical('must supply a name in createLUN()')
            return False

        ## Create LUN Parameters
        pool = self.getPool(pool)
        if not pool:
            # Failed to get pool, by name
            # does the pool exist?
            return False  # Should we throw an exception?
        poolDict = {}
        poolDict['id'] = pool['id']

        # create lunParameters Structure
        lpDict = {}
        lpDict['size'] = size
        lpDict['pool'] = poolDict
        if isThinEnabled:
            lpDict['isThinEnabled'] = isThinEnabled

        # Form the message body for lunCreate API
        bodyDict = {}
        bodyDict['name'] = name
        if description:
            description = description[0:170]  # max 170 characters
            bodyDict['description'] = description
        bodyDict['lunParameters'] = lpDict
        body = json.dumps(bodyDict)
        # print(body)

        # Create the LUN
        u = self.urlbase + '/api/types/storageResource/action/createLun'
        r = self.session.post(url=u, data=body, headers=self.headers, verify=False)
        if r.ok:
            js = r.json()
            lunID = js['content']['storageResource']['id']
            returnCode = lunID
        else:
            self._printError("POST", r)
            returnCode = False

        return returnCode

    def deleteLUN(self, name):
        rc = self.deleteStorage(name=name, resourceType='lun',force=True)
        return rc

    def deleteFS(self, name):
        rc = self.deleteStorage(name=name, resourceType='fs',force=True)
        return rc

    def deleteNFSShare(self,name=None):
        """
        Delete an NFS Share
        Preserve the associated file system
        :param name:  string - share name
        :return: True or False
        """
        if not name:
            logging.warning('need to pass a name to deleteNFSShare')
            return False

        id = (self.getNFSShare(name))['id']
        if not id:
            logging.warning("can't find id associated with share named {}".format(name))
        u = self.urlbase + '/api/instances/nfsShare/{}'.format(id)
        body = ""
        # Delete
        r = self.session.delete(url=u, data=body, headers=self.headers, verify=False)
        if r.ok:
            retCode = True
        else:
            logging.warning('failed to delete name: {} id: {}'.format( name, id))
            retCode = False
        return (retCode)



    def deleteStorage(self, id=None, name=None, resourceType='lun', force=False ):
        '''

        :param lunID: an internal ID which references the resource of filesystem ID, typically as returned by _getIDs()
        :param lunName: name of the resource to be deleted
        :param resourceType: lun|block -or- fs|file --- defaults to lun
        :return: True on success; else False
        '''
        resourceType.lower()  # make it simple on our users
        storageResource = {}
        if not resourceType in ('lun', 'fs', 'filesystem'):
            logging.error(
                "must pass valid resourceType to deleteStorage 'lun','block','fs',or 'file', you passed{}".format(
                    resourceType))
            return False

        sr = None
        bodyDict = {}
        if force:
            bodyDict['forceSnapDeletion'] = 'true'
            bodyDict['forceVvolDeletion'] = 'true'
        if resourceType == 'lun':
            sr = self.getLUN(name)
            # Create the command body - current behavior is
            # to dump all snaps and vvols associated with this LUN

        elif resourceType == 'fs':
            sr = self.getFS(name)

        ### Is this a different ID for LUNs and File systems (!!??)
        id = sr['storageResource']['id']

        # we can be called with an ID or a Name
        # if both are specified, default to ID
        # at least one must be provided


        # following code is germane to deleting a LUN or filesystem

        body = json.dumps(bodyDict)

        u = self.urlbase + '/api/instances/storageResource/{}'.format(id)
        # Delete
        r = self.session.delete(url=u, data=body, headers=self.headers, verify=False)
        if r.ok:
            retCode = True
        else:
            logging.warning('failed to retrieve {} name: {} id: {}'.format(resourceType, name, id))
            retCode = False
        return (retCode)

    def getNASServers(self):
        """
            return: list of NAS servers on Success
                    False on failure
        """
        retCode = []
        u = self.urlbase + '/api/types/nasServer/instances'
        ids = self._getIds(u)
        fields = 'id,name,health,homeSP,currentSP,pool,sizeAllocated,isReplicationEnabled,isReplicationDestination,\
        replicationType,defaultUnixUser,defaultWindowsUser,currentUnixDirectoryService,isMultiProtocolEnabled,\
        isWindowsToUnixUsernameMappingEnabled,allowUnmappedUser,cifsServer,preferredInterfaceSettings,fileDNSServer,\
        fileInterface,virusChecker'
        # get rid of the blanks in the string
        fields = fields.replace(" ", "")
        fields = fields.replace('\i', '')
        Valid = False
        for id in ids:
            u = self.urlbase + '/api/instances/nasServer/{}'.format(id) + '?fields=' + fields
            nasJson = self._getJSON(u)
            if nasJson:
                Valid = True
                retCode.append(nasJson)
        if not Valid:
            retCode = False
        return retCode

    def createFileSystem(self, name, pool, size, nasServer, description='', isThinEnabled='true', sizeAllocated=None):
        '''
        Create a Filesytem
        :param description:
        required:
           name - String - up to 95 characters
           pool
           nasServer - JSON, encoded as String, as returned from GetNASByName()
        :param pool:
        :param size:
        :param NasServer:
        :return:
        '''
        # build the fileSystemsParameters Structure
        if size < 3 * self.oneGB:
            # min fs size is 3G
            size = 3 * self.oneGB

        returnCode = False
        logging.debug('createFileSystem {}'.format(name))

        ## Need to create a dictionary representation for the JSON {"id":"poolID"}
        ## Change the pool Variable to contain just that representation

        poolDict = {}
        rpool = self.getPool(pool)
        poolDict['id'] = rpool['id']
        poolDict['name'] = rpool['name']
        logging.debug(poolDict)

        ## Need to create a dictionary representation for the JSON { {"id":"nasServerID"}
        ## change the NasServer variable

        # nasServerDict = {}
        # nasServerDict['id'] = json.loads(nasServer)['id']
        # nasServer = nasServerDict
        # del nasServerDict
        logging.debug(nasServer)

        # Create the Body of the Request
        # Starting with the File System Parameters Structure
        fsp = {}
        fsp['pool'] = poolDict
        fsp['size'] = size
        fsp['supportedProtocols'] = 0
        fsp['isThinEnabled'] = 'true'
        ### The API doesn't seem to like the full nasServer.  Abbreviate it.
        myNasServer = {}
        myNasServer['name'] = nasServer['name']
        myNasServer['id'] = nasServer['id']
        fsp['nasServer'] = myNasServer
        body = {}
        body['name'] = name
        body['description'] = description
        body['fsParameters'] = fsp
        jsonbody = json.dumps(body)
        logging.debug(jsonbody)

        u = self.urlbase + '/api/types/storageResource/action/createFilesystem'
        r = self.session.post(url=u, data=jsonbody, headers=self.headers, verify=False)
        if r.ok:
            js = r.json()
            # js = json.loads(r.content.decode('utf-8'))
            lunID = js['content']['storageResource']['id']
            returnCode = lunID
        else:
            self._printError("POST", r)
        return returnCode

    def createNFSShareFromSnap(self, name, snap, protocol='nfs', path='/', description=""):
        '''
        Create a new share
        At this moment, we only know about NFS version 3 shares
        And no attempt is made to control access
        Access is available to everyone.
        :param name: String name of the new share
        :param protocol: Sting - ignored for now, must be nfs
        :param path:
        :param description:
        :param snap: python structure of a Unity File System Snapshot
        :return: share object or False
        '''
        returnCode = False
        logging.debug('createShare name:{} snap:{}'.format(name,snap))
        if not snap or not name:
            logging.warning('createNFSShareFromSnap - must include name and filesystem')
            return False
        if not snap['id'] or not snap['name']:
            logging.warning('createNFSShareFromSnap - snap structure looks incomplete (needs id and name)')
            return False

        # Check to see if this share name already exists
        if self.getNFSShare(name):
            logging.warning('share {} exists'.format(name))
        else:
            logging.debug('validated that {} in not an existing share'.format(name))

        # Build the arguments to create and NFS Share
        body = {}
        myfs = {}
        myfs['id']=snap['id']
        # myfs['name'] = snap['name']
        body['snap']=myfs
        body['path']=path
        body['name']=name
        body['description']=description
        # This needs to be corrected!
        # For initial testing grant all access to all hosts.
        body['defaultAccess']=NFSShareDefaultAccessEnum.Root.value
        body['minSecurity'] = NFSShareSecurityEnum.Sys.value

        jsonbody = json.dumps(body)
        # logging.debug(jsonbody)

        u = self.urlbase + '/api/types/nfsShare/instances'
        r = self.session.post(url=u, data=jsonbody, headers=self.headers, verify=False)
        if r.ok:
            js = r.json()
            # js = json.loads(r.content.decode('utf-8'))
            nfsShareID = js['content']['id']
            returnCode = nfsShareID
        else:
            self._printError("POST", r)
        return returnCode


    def getNFSShare(self,name):
        # Not implemented.
        return self.getStorageDict(resourceType="nfsshare", name=name)

    def getNAS(self, name):
        return self.getStorageDict(resourceType="nas", name=name)

    def getNFS(self, name):
        return self.getStorageDict(resourceType="nfs", name=name)

    def getFS(self, name):
        return self.getStorageDict(resourceType="fs", name=name)

    def getLUN(self, name):
        return self.getStorageDict(resourceType="lun", name=name)

    def getPool(self, name):
        return (self.getStorageDict(resourceType="pool", name=name))

    def getStorageResource(self, name):
        return (self.getStorageDict(resourceType="sr", name=name))

    def getSnap(self, name):
        return (self.getStorageDict(resourceType="snap", name=name))

    def getStorageDict(self, resourceType="lun", name="", id=""):
        """

        :param self:
        :param resourceType: "lun" or "fs" or "nas"
        :param name: the resource Name   [ Note - only need name or id, not both ]
        :param id: the resource ID
        :return: dictionary for the storage resource or None
        """
        lunfields = 'id,name,health,description,type,sizeTotal,sizeUsed,sizeAllocated,perTierSizeUsed,isThinEnabled,\
            storageResource,pool,wwn,tieringPolicy,defaultNode,currentNode,snapSchedule,isSnapSchedulePaused,\
            ioLimitPolicy,metadataSize,metadataSizeAllocated,snapWwn,snapsSize,snapsSizeAllocated,hostAccess,snapCount'
        nfsfields = (
            'id,hostName,nasServer,fileInterfaces,nfsv4Enabled,isSecureEnabled,kdcType,servicePrincipalName'
            ',isExtendedCredentialsEnabled,credentialsCacheTTL'
        )
        fsfields = 'id,health,name,description,type,sizeTotal,sizeUsed,sizeAllocated,isReadOnly,isThinEnabled,\
            storageResource,pool,nasServer,tieringPolicy,supportedProtocols,metadataSize,metadataSizeAllocated'
        nasfields = (
            'id,name,health,homeSP,currentSP,pool,sizeAllocated,isReplicationEnabled,replicationType'
            ',defaultUnixUser,defaultWindowsUser,currentUnixDirectoryService,isMultiProtocolEnabled'
            ',isWindowsToUnixUsernameMappingEnabled,allowUnmappedUser,cifsServer,preferredInterfaceSettings'
            ',fileDNSServer,fileInterface,virusChecker'
        )
        poolfields = (
            'id,health,name,description,storageResourceType,raidType,sizeFree,sizeUsed,sizeSubscribed'
            ',alertThreshold,isFASTCacheEnabled,tiers,creationTime,isEmpty,poolFastVP,isHarvestEnabled'
            ',harvestState,isSnapHarvestEnabled,poolSpaceHarvestHighThreshold,poolSpaceHarvestLowThreshold'
            ',snapSpaceHarvestHighThreshold,snapSpaceHarvestLowThreshold,metadataSizeSubscribed'
            ',snapSizeSubscribed,metadataSizeUsed,snapSizeUsed,rebalanceProgress'
        )
        srfields = (
            'id,health,name,description,type,isReplicationDestination,replicationType,sizeTotal,sizeUsed'
            ',sizeAllocated,thinStatus,esxFilesystemMajorVersion,esxFilesystemBlockSize,snapSchedule'
            ',isSnapSchedulePaused'
        )

        nfssharefields = (
            'id,type,role,filesystem,snap,name,path,exportPaths,description,isReadOnly'
            ',creationTime,modificationTime,defaultAccess,minSecurity,noAccessHosts,readOnlyHosts'
            ',readWriteHosts,rootAccessHosts,hostAccesses'
        )

        snapfields = (
            'id,name,description,storageResource,lun,snapGroup,parentSnap,creationTime,expirationTime'
            ',creatorType,creatorUser,creatorSchedule,isSystemSnap,isModifiable,attachedWWN,accessType'
            ',isReadOnly,lastWritableTime,isModified,isAutoDelete,state,size,ioLimitPolicy'
        )

        resourceType = resourceType.lower()
        if resourceType == 'lun':
            # Here when we are looking for a LUN
            urlAPI = '/api/types/lun/instances'
            fields = lunfields
        elif resourceType == 'pool':
            urlAPI = '/api/types/pool/instances'
            fields = poolfields
        elif resourceType == 'nfs':
            # Here when we are looking for a file system
            urlAPI = '/api/types/nfsServer/instances'
            fields = nfsfields
        elif resourceType == 'fs':
            # Here when we are looking for a file system
            urlAPI = '/api/types/filesystem/instances'
            fields = fsfields
        elif resourceType == 'sr':
            # For Unity StorageResources include LUNs, Consistency Groups, Filesystems
            # VMware NFS and VMDS, VVOL file and VVOL Block
            urlAPI = '/api/types/storageResource/instances'
            fields = srfields
        elif resourceType == 'nas':
            # Here when we need a NAS instance ( the filer/data mover )
            urlAPI = '/api/types/nasServer/instances'
            fields = nasfields
        elif resourceType == 'nfsshare':
            urlAPI = '/api/types/nfsShare/instances'
            fields = nfssharefields
        elif resourceType == 'snap':
            # Here when we
            urlAPI = '/api/types/snap/instances'
            fields = snapfields
        else:
            logging.critical('unknown resource type {} passed to getStorageDict'.format(resourceType))
            return False

        if id != "":
            # get by id
            u = self.urlbase + urlAPI + '?fields=' + fields + '&filter=id eq "{}"'.format(id)
        elif name != "":
            # get by name
            if resourceType == 'nfs':
                u = self.urlbase + urlAPI + '?fields=' + fields + '&filter=hostName eq "{}"'.format(name)
            else:
                u = self.urlbase + urlAPI + '?fields=' + fields + '&filter=name eq "{}"'.format(name)
        else:
            return False
        # get the storage Resource based on this name
        sr = self.session.get(url=u)
        if sr.ok:
            tmpDict = sr.json()
            if tmpDict['entries']:
                srDict = json.loads(sr.content.decode('utf-8'))['entries'][0]['content']
            else:
                logging.debug('No value returned from the array for name {}'.format(name))
                srDict = False
            return (srDict)
        else:
            self._printError('GET', sr)
            return None


