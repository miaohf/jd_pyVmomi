#!/usr/bin/env python3

"""
Written by jdreal.
Github:

Get the information about vm and its datastore.
"""

from src_share import vcenter_instance_check, get_obj_id
from pyVmomi import vim


def vmsdsinfo(vm, cloudid):
    vmDict = {}
    # instanceUuid: VC-specific identifier of the virtual machine`
    # uuid: Virtual machine BIOS identification
    # vmDict['VMID'] = vm.summary.config.instanceUuid
    vmDict['VMID'] = get_obj_id.id(vm)

    # datastore uuid: The universally unique identifier assigned to VMFS.
    # vmDict['DSID'] = vm.datastore[0].info.vmfs.uuid
    global d
    d = {}
    count = 1
    for ds in vm.datastore:
        did = 'Datastore_' + str(count)
        d[did] = get_obj_id.id(ds)
        count += 1

    vmDict['DSID'] = d
    vmDict['CLOUD'] = cloudid
    vmDict['CHKTIME'] = ''

    return vmDict


def get_vm_vmsdsmap(cloudid):
    """
    获取虚机以及它所使用的存储信息
    """

    si_content = vcenter_instance_check.vc_instance_check(cloudid)

    container = si_content.rootFolder
    container_view = si_content.viewManager.CreateContainerView(
        container, [vim.VirtualMachine], True)
    # 获取所有的虚拟机
    vms = container_view.view

    vmsdsDict = {}
    for vm in vms:
        vmsdsDict['VM_' + vm.name] = vmsdsinfo(vm, cloudid)

    return vmsdsDict


if __name__ == "__main__":
    cloudid = 7
    print(get_vm_vmsdsmap(cloudid))
