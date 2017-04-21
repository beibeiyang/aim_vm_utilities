#!/usr/bin/env python

# Copyright (c) 2017 Dell, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Python program for taking, removing and listing snapshots of all VMs from a VM folder in vCenter
"""

import atexit
import ssl
import time
import sys

from pyVim.connect import SmartConnect, Disconnect, GetSi
from pyVmomi import vmodl
from pyVmomi import vim

from tools import cli, folder, tasks


def set_sslcontext(args):
    sslContext = None

    if args.disable_ssl_verification.lower() == 'true':
        sslContext = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        sslContext.verify_mode = ssl.CERT_NONE

    return sslContext

def get_vms_info(vm, depth= 1):
    """
    Print information for a particular virtual machine or recurse into a folder
     with depth protection
    """
    maxdepth = 5

    if depth > maxdepth:
        return

    # if this is a group it will have children. if it does, recurse into them
    # and then return
    if hasattr(vm, 'childEntity'):

        vmList = vm.childEntity
        for c in vmList:
            get_vms_info(c, depth+1)

    else:
        summary = vm.summary
        # print("Name       : ", summary.config.name)
        return (summary.config.name, summary.config.instanceUuid)


def get_vm_names_in_folder(content, foldername):
    """
    List the names of all the VMs in a folder
    :param content: service instance content
    :param foldername: the foldername to list all the VMs, e.g., aim_vms
    :return: names of all the vms in @foldername
    """
    container = folder.find_by_name(content.rootFolder, foldername)
    viewType = [vim.VirtualMachine]  # object types to look for
    recursive = True  # whether we should look into it recursively
    containerView = content.viewManager.CreateContainerView(
        container, viewType, recursive)

    children = containerView.view

    vms = {}
    for child in children:
        vmname, iuuid = get_vms_info(child)
        vms[vmname] = iuuid

    return vms


def get_args():
    parser = cli.build_arg_parser()
    parser.add_argument('-S', '--disable_ssl_verification',
                        required=False,
                        default="True",
                        action='store',
                        help='Disable ssl host certificate verification (default to True)')
    parser.add_argument('-f', '--aim_folder', required=True,
                        help='Name of the folder which stores all the VMs in vCenter to snapshot, e.g., "aim-demo-01"')
    parser.add_argument('-op', '--operation', required=False, default="create",
                        help='Type of operation, can only be one of the following: create, remove, or list (default as create)')
    parser.add_argument('-sn', '--snapshot_name', required=False, default=time.strftime("%m-%d-%Y"),
                        help='Snapshot name, default to be the current date in MM-DD-YYYY format')
    parser.add_argument('-sm', '--snapshot_memory', required=False, default="False",
                        help='whether to snapshot virtual machine\'s memory, default to False; use with "create" operation')
    parser.add_argument('-sq', '--snapshot_quiesce', required=False, default="False",
                        help='whether to quiesce guest file system (needs VMWare Tools installed on VM), default to False; '
                             'use with "create" operation')

    my_args = parser.parse_args()
    return cli.prompt_for_password(my_args)


def get_obj(content, vimtype, iuuid, name):
    """
     Get the vsphere object associated with a given text name
    """
    obj = None
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for c in container.view:
        # print ("*"*30)
        # print(c.name)
        # print(c.config.instanceUuid)
        # print(c)
        if c.config.instanceUuid == iuuid and c.name == name:
            obj = c
            break
    if not obj:
        print("Could not find {}: {}".format(vimtype, name))
        raise SystemExit(-1)
    return obj


def get_snapshots(vm):
    if vm.snapshot:
        return get_snapshots_paths_recursively(vm.snapshot.rootSnapshotList, '')
    else:
        print("\t No snapshots")


def get_snapshots_paths_recursively(snapshots, snapshot_location):
    snapshot_paths = []

    if not snapshots:
        return snapshot_paths

    for snapshot in snapshots:
        if snapshot_location:
            current_snapshot_path = snapshot_location + '/' + snapshot.name
        else:
            current_snapshot_path = snapshot.name

        snapshot_paths.append(current_snapshot_path)
        snapshot_paths = snapshot_paths + get_snapshots_paths_recursively(snapshot.childSnapshotList, current_snapshot_path)

    return snapshot_paths


def remove_snapshots(service_instance, vm, snapshot_name):
    if vm.snapshot:
        return remove_snapshots_recursively(service_instance, vm.snapshot.rootSnapshotList, '', snapshot_name)


def remove_snapshots_recursively(service_instance, snapshots, snapshot_location, snapshot_name):
    if not snapshots:
        return

    for snapshot in snapshots:
        if snapshot_location:
            current_snapshot_path = snapshot_location + '/' + snapshot.name
        else:
            current_snapshot_path = snapshot.name

        if snapshot_name == snapshot.name:
            snap_obj = snapshot.snapshot
            print ("\t{}/{}\n\t\tRemoving snapshot {}".format(snapshot_location, snapshot_name, snap_obj))
            tasks.wait_for_tasks(service_instance, [snap_obj.RemoveSnapshot_Task(removeChildren=True)])

        else:
            remove_snapshots_recursively(service_instance, snapshot.childSnapshotList, current_snapshot_path, snapshot_name )


def main():
    args = get_args()

    try:
        service_instance = SmartConnect(host=args.host,
                                        user=args.user,
                                        pwd=args.password,
                                        port=int(args.port),
                                        sslContext=set_sslcontext(args))

        # disconnect vc
        atexit.register(Disconnect, service_instance)

        content = service_instance.RetrieveContent()

        print ("Identify VMs in folder {}".format(args.aim_folder))

        vmsDict = get_vm_names_in_folder (content,
                                           foldername=args.aim_folder)

        #print ("VM names: ", vmsNames)
        n = len(vmsDict)
        vmNames = sorted(vmsDict.keys())

        print ("Fetched {} VMs in folder {}".format(n, args.aim_folder))

        # for debug purposes
        #vmsNames = vmsNames[:4]
        print ("Identified VMs:", vmNames)

        operation = args.operation.lower()

        print ("Begin to {} snapshot VMs in folder {}".format(operation, args.aim_folder))

        i = 0
        for vname in vmNames:
            iuuid = vmsDict[vname]
            print ("{} snapshot {}/{}: {}".format(operation.capitalize(), i + 1, n, vname))
            vm = get_obj(content, [vim.VirtualMachine], iuuid, vname)

            if vm.config.template:
                print ("\t ... skip template")
                continue
            if operation == "create":
                snapshot_memory = args.snapshot_memory.strip().lower() == "true"
                snapshot_quiesce = args.snapshot_quiesce.strip().lower() == "true"
                tasks.wait_for_tasks(service_instance, [vm.CreateSnapshot(args.snapshot_name, description="",
                                                                          memory=snapshot_memory, quiesce=snapshot_quiesce)
                                                        ])
            elif operation == "remove":
                remove_snapshots(service_instance, vm, args.snapshot_name)

            elif operation == "list":
                # list snapshots
                snapshot_paths = get_snapshots(vm)
                if snapshot_paths:
                    for snapshot_path in snapshot_paths:
                        print ('\t {}'.format(snapshot_path))

            else:
                print("Operation must be one of the following: create, remove, or list")
                sys.exit(1)
            i += 1



    except vmodl.MethodFault as e:
        print ("Caught vmodl fault: %s" % e.msg)
        return 1

    except Exception as e:
        if str(e).startswith("'vim.Task'"):
            return 1
        print ("Caught exception: %s" % e.msg)
        return 1


# Start program
if __name__ == "__main__":
    main()
