# pu  Python bindings for EMC Unity
Python bindings to the EMC Unity NAS array.

## Description
21 July 2016

The [EMC Unity](https://www.emc.com/en-us/storage/unity.htm#tab2=0&tab3=0&collapse=) 
family of arrays deliver a mid-tier storage platform 
including NAS, Block and VMware vVol support.  The family is available 
as a hardware or virtual appliance.

These python bindings call the Unity REST API and return python dictionaries.

### Intention
The author's desire is to enable automation of the high frequency activities
such as create/delete of snapshots, LUNs, File systems and vVols. 
Other aspects of the API less frequent and perhaps less interesting for automation.
For example, how often do you need to alter the DNS server or NTP server of a storage array?

Someday, we may build this out as a complete set of bindings to the REST API, but we're starting at those actions with the highest benefit from automation.
  
### Requirements
pip install requests
pip install json


## Usage Instructions

### Login and create a session / array object

```python
from pu.unityarray import unityarray
from pu.snap import snap


host = "10.0.0.3"
login = "admin"
password = "Password123#"

a = unityarray(ipaddr=host, user=user, password=password)


```

### Create a LUN, Get LUN information, Delete a LUN

```python     
def printTestResult(result, name=""):
    if result:
        logging.info('SUCCESS - {}'.format(name))
    else:
        logging.info('FAILED - {}'.format(name))
       
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
```

### Create a File System, Delete a File System
```python
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
```


### Create and Delete Snapshots against a LUN
```python
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
    rc = a.deleteLUN(name=lname)
    printTestResult(rc, 'deleteLUN({})'.format(lname))
```

### Create and Delete File System Snapshots
```python
timestamp = time.strftime('%d%M%Y_%H%M%S',time.localtime())
fsname = 'fs_snap_test_{}_'.format(timestamp)
fsdescr = 'fs {} created to be the basis for snap testing'.format(fsname)
fspool = 'flash01'
fssize = a.threeGB
nasname = 'nas02'

fsNasServer = a.getNAS(nasname)
if fsNasServer:
    logging.info('creating file system {}'.format(fsname) + 'this takes about 60 seconds ...')
    f = a.createFileSystem(name=fsname, pool=fspool, size=fssize, nasServer=fsNasServer, description=fsdescr)
    fs = a.getFS(fsname)
    printTestResult((fsname == fs['name']), 'getFS()',fsname)

    # Snap the Filesystem
    logging.info('creating snapshot of file system: {}'.format(fsname))
    snapname = "snap_" + fsname
    s = a.createsnap(fsname,snapname)
    printTestResult('s','createsnap()')
    exit()
    # Delete the Snap
    logging.info('deleting snapshot of file system: {}'.format(fsname))
    rc = a.deleteSnap(snapName=snapname)
    printTestResult(rc,'deleteFS({})'.format(fsname))

    # Delete the File System
    a.deleteFS(fsname)
else:
    logging.error("couldn't find NAS server {}".format(nasname))
    logging.info('FAILED - {}'.format('getNAS({})'.format(nasname)))
```

## Contribution
Create a fork of the project into your own reposity. Make all your necessary changes and create a pull request with a description on what was added or removed and details explaining the changes in lines of code. If approved, project owners will merge it.
Licensing
---------
**PLACE A COPY OF THE [APACHE LICENSE](http://emccode.github.io/sampledocs/LICENSE "LICENSE") FILE IN YOUR PROJECT**

Licensed under the Apache License, Version 2.0 (the “License”); you may not use this file except in compliance with the License. You may obtain a copy of the License at <http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.


Support
-------
Please file bugs and issues at the Github issues page.