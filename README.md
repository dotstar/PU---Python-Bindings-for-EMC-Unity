# PU ---Python-Bindings-for-EMC-Unity
Python bindings to the EMC Unity NAS array.

## Background
12 July 2016

The [EMC Unity](https://www.emc.com/en-us/storage/unity.htm#tab2=0&tab3=0&collapse=) 
family of arrays deliver a mid-tier storage platform 
including NAS, Block and VMware vVol support.  The family is available 
as a hardware or virtual appliance.

These python bindings call the Unity REST API and return python dictionaries.

## Intention
The author's desire is to enable automation of the high frequency activities
such as create/delete of snapshots, LUNs, File systems and vVols. 
Other aspects of the API less frequent and perhaps less interesting for automation.
For example, how often do you need to alter the DNS server or NTP server of a storage array?

Someday, we may build this out as a complete set of bindings to the REST API, but we're starting at those actions with the highest benefit from automation.
  

## Examples

### Login and create a session / array object

```python
import pu.snap
import pu.array

host = "10.0.0.3"
login = "admin"
password = "Password123#"

a = pu.unityarray.unityarray(ipaddr=host, user=user, password=password)


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

### create a File System, delete a File System
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
    rc = a.deleteStorage(name=lname)
    printTestResult(rc, 'deleteStorage({})'.format(lname))
```