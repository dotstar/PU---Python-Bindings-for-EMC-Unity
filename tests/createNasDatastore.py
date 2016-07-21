#!/usr/bin/env python
# ask VMware to add a NAS share as a datastore
# Originally from:
# William Lam
# www.virtuallyghetto.com

"""
vSphere Python SDK program for listing all ESXi datastores and their
associated devices
"""
import argparse
import atexit
import json
import ssl

from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim

# from tools import cli


# http://stackoverflow.com/questions/1094841/
def sizeof_fmt(num):
    """
    Returns the human readable version of a file size

    :param num:
    :return:
    """
    for item in ['bytes', 'KB', 'MB', 'GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, item)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


def print_fs(host_fs):
    """
    Prints the host file system volume info

    :param host_fs:
    :return:
    """
    print("{}\t{}\t".format("Datastore:     ", host_fs.volume.name))
    print("{}\t{}\t".format("UUID:          ", host_fs.volume.uuid))
    print("{}\t{}\t".format("Capacity:      ", sizeof_fmt(
        host_fs.volume.capacity)))
    print("{}\t{}\t".format("VMFS Version:  ", host_fs.volume.version))
    print("{}\t{}\t".format("Is Local VMFS: ", host_fs.volume.local))
    print("{}\t{}\t".format("SSD:           ", host_fs.volume.ssd))


def main():
    """
   Simple command-line program for listing all ESXi datastores and their
   associated devices
   """

    host = '192.168.23.10'  # vCenter
    user = "codetest@vsphere.local"     # Administrative
    password = "Password123#"
    port = 443
    sslContext = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    sslContext.verify_mode = ssl.CERT_NONE
    json = False

    try:
        service_instance = connect.SmartConnect(host=host,
                                                user=user,
                                                pwd=password,
                                                port=port,
                                                sslContext=sslContext)
        if not service_instance:
            print("Could not connect to the specified host using specified "
                  "username and password")
            return -1

        atexit.register(connect.Disconnect, service_instance)

        content = service_instance.RetrieveContent()
        # Search for all ESXi hosts
        objview = content.viewManager.CreateContainerView(content.rootFolder,
                                                          [vim.HostSystem],
                                                          True)
        esxi_hosts = objview.view
        objview = content.viewManager.CreateContainerView(content.rootFolder,
                                                          [vim.Datacenter],
                                                          True)
        objview.Destroy()

        datastore = ""
        # Add an NFS datastore on each host ...
        for host in esxi_hosts:
            nasServer = "192.168.23.22"
            nfsPath = "/cddtest"
            localPath = "cddtest"
            print("creating datastore {} on host: {}".format(localpath, host.name))
            accessMode = "readWrite" ### ???
            # Build the Specification and add the store ...
            spec=vim.host.NasVolume.Specification()
            spec.remoteHost=nasServer
            spec.remotePath=nfsPath
            spec.localPath=localPath
            spec.accessMode=accessMode
            datastore = host.configManager.datastoreSystem.CreateNasDatastore(spec)
            print(datastore)
    except vmodl.MethodFault as error:
        print("Caught vmodl fault : " + error.msg)
        return -1

    # Pause
    r = input('pausing ... hit enter to continue.')
    for host in esxi_hosts:

    return 0

# Start program
if __name__ == "__main__":
    main()
