from enum import Enum

class NFSShareRoleEnum(Enum):
    Production = 0
    Backup = 1

class NFSShareDefaultAccessEnum(Enum):
    NoAccess=0
    ReadOnly=1
    ReadWrite=2
    Root=3

class NFSShareSecurityEnum(Enum):
    Sys = 0
    Kerberos = 1
    KerberosWithIntegrity = 2
    KerberosWithEncryption = 3

class NFSTypeEnum(Enum):
    Nfs_Share = 1
    Vmware_Nfs = 2
    Nfs_Snapshot = 3

class FilesystemSnapAccessTypeEnum(Enum):
    Checkpoint = 1
    Protocol = 2

class FilesystemTypeEnum(Enum):
    FileSystem = 1
    VMware = 2