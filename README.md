# AIM Utility Scripts

Tested with Python 3.5 and pyvmomi 6.5

Copyright (c) 2017 Dell, Inc.

For any general or technical questions, email: Beibei.Yang@dell.com

## Script: ```aim_batch_snapshot_vms.py```

This script batch snapshots all VMs in a vCenter folder with the same snapshot
name. Supports batch operations such as create snapshots, remove snapshots and
list snapshots.


```
$ python aim_batch_snapshot_vms.py -h
usage: aim_batch_snapshot_vms.py [-h] -s HOST [-o PORT] -u USER [-p PASSWORD]
                                 [-S DISABLE_SSL_VERIFICATION] -f AIM_FOLDER
                                 [-op OPERATION] [-sn SNAPSHOT_NAME]
                                 [-sm SNAPSHOT_MEMORY] [-sq SNAPSHOT_QUIESCE]

Standard Arguments for talking to vCenter

optional arguments:
  -h, --help            show this help message and exit
  -s HOST, --host HOST  vSphere service to connect to
  -o PORT, --port PORT  Port to connect on
  -u USER, --user USER  User name to use when connecting to host
  -p PASSWORD, --password PASSWORD
                        Password to use when connecting to host
  -S DISABLE_SSL_VERIFICATION, --disable_ssl_verification DISABLE_SSL_VERIFICATION
                        Disable ssl host certificate verification (default to True)
  -f AIM_FOLDER, --aim_folder AIM_FOLDER
                        Name of the folder which stores all the VMs in vCenter
                        to snapshot, e.g., "aim-demo-01"
  -op OPERATION, --operation OPERATION
                        Type of operation, can only be one of the following:
                        create, remove, or list (default to create)
  -sn SNAPSHOT_NAME, --snapshot_name SNAPSHOT_NAME
                        Snapshot name, default to be the current date in MM-
                        DD-YYYY format
  -sm SNAPSHOT_MEMORY, --snapshot_memory SNAPSHOT_MEMORY
                        whether to snapshot virtual machine's memory, default
                        as False; use with "create" operation
  -sq SNAPSHOT_QUIESCE, --snapshot_quiesce SNAPSHOT_QUIESCE
                        whether to quiesce guest file system (needs VMWare
                        Tools installed on VM), default to False; use with
                        "create" operation
```

For example, to snapshot all VMs in tme-aim folder with a given snapshot name
(-sn) and snapshot the VM's memory (-sm True):
```
    python aim_batch_snapshot_vms.py -s aim.lab.emc.com
    -u user@vsphere.local -p <password> -f tme-aim
    -sn "01-20-2017: Test snapshot" -sm True
```

To list snapshots of all VMs in tme-aim folder:
```
    python aim_batch_snapshot_vms.py -s aim.lab.emc.com
    -u user@vsphere.local -p <password> -f tme-aim -op=list
```

To remove snapshots of all VMs in tme-aim folder with a given snapshot name (-sn):
```
    python aim_batch_snapshot_vms.py -s aim.lab.emc.com
    -u user@vsphere.local -p <password> -f tme-aim
    -op remove -sn "01-20-2017: Test snapshot"
```

## Script: ```aim_get_vmfolder_resources_stats.py```

This script retrieves vCPU, Memory and Disk provision stats of all VMs from a
VM folder in vCenter. Given a folder name in vSphere, the script will print out
the provisioned vCPU, memory and Disk of every VM in that folder and spit out
the sum at the end.

```
$ python aim_get_vmfolder_resources_stats.py -h
usage: aim_get_vmfolder_resources_stats.py [-h] -s HOST [-o PORT] -u USER
                                           [-p PASSWORD]
                                           [-S DISABLE_SSL_VERIFICATION] -f
                                           AIM_FOLDER

Standard Arguments for talking to vCenter

optional arguments:
  -h, --help            show this help message and exit
  -s HOST, --host HOST  vSphere service to connect to
  -o PORT, --port PORT  Port to connect on
  -u USER, --user USER  User name to use when connecting to host
  -p PASSWORD, --password PASSWORD
                        Password to use when connecting to host
  -S DISABLE_SSL_VERIFICATION, --disable_ssl_verification DISABLE_SSL_VERIFICATION
                        Disable ssl host certificate verification (default to True)
  -f AIM_FOLDER, --aim_folder AIM_FOLDER
                        Name of the folder which stores all the VMs in vCenter
                        to snapshot, e.g., "aim-demo-01"
```

For example, the following command will print out the provisioned vCPU, memory
and Disk of every VM in the ODC folder and spit out the sum at the end:
```
    python aim_get_vmfolder_resources_stats.py -s aim.lab.emc.com
    -u user@vsphere.local -p <password> -f hwx01m20170101123456
```
