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
Python program for getting provision stats of vCPU, Memory and Disk of all VMs inside a VM folder
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
        print ("="*30)
        print("Name\t: ", summary.config.name)
        print("# vCPU\t: ", summary.config.numCpu)
        print("# memory (MB)\t: ", summary.config.memorySizeMB)
        #print("summary.vm.guest.disk\t:", summary.vm.guest.disk)
        vmdisksum = 0.0
        for device in vm.config.hardware.device:
            if type(device).__name__ == 'vim.vm.device.VirtualDisk':
                # device.deviceInfo.summary looks like '26,214,400 KB', convert to numeric GB
                disk = float(device.deviceInfo.summary[:-3].replace(',',''))/1024/1024
                print('%s (GB)\t: %f' % (device.deviceInfo.label, disk))
                vmdisksum += disk
        return (summary.config.name, summary.config.numCpu, summary.config.memorySizeMB, vmdisksum)


def get_vm_stats_in_folder(content, foldername):
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

    totalCpu = 0.0
    totalMemory = 0.0
    totalDisk = 0.0
    for child in children:
        vmname, cpu, memory, disk = get_vms_info(child)
        totalCpu += cpu
        totalMemory += memory
        totalDisk += disk
    return (len(children), totalCpu, totalMemory/1024, totalDisk)


def get_args():
    parser = cli.build_arg_parser()
    parser.add_argument('-S', '--disable_ssl_verification',
                        required=False,
                        default="True",
                        action='store',
                        help='Disable ssl host certificate verification')
    parser.add_argument('-f', '--aim_folder', required=True,
                        help='Name of the folder which stores all the VMs in vCenter to snapshot, e.g., "aim-demo-01"')

    my_args = parser.parse_args()
    return cli.prompt_for_password(my_args)


def get_obj(content, vimtype, name):
    """
     Get the vsphere object associated with a given text name
    """
    obj = None
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    if not obj:
        print("Could not find {}: {}".format(vimtype, name))
        raise SystemExit(-1)
    return obj



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

        n, totalCpu, totalMemory, totalDisk = get_vm_stats_in_folder (content,
                                    foldername=args.aim_folder)
        print ("*"*30)
        print ("FINAL STATS")
        print ("*"*30)
        print ("Identified %i VMs" % n)
        print ("Total vCPU: ", totalCpu)
        print ("Total Memory (GB): ", totalMemory)
        print ("Total Disk (GB): ", totalDisk)


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
