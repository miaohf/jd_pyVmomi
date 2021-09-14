#!/usr/bin/env python3

"""
Written by jdreal.
Github:

Get the information about vm and its datastore.
"""

from src_share import get_obj_id, vcenter_instance_check
from pyVmomi import vim


def vminfo(vm, cloudid):
    vmSummary = vm.summary
    vmConfig = vm.config

    # areaID = str(vm.parent.parent).split(":")[1].strip("'")
    # sysID = str(vm.parent).split(":")[1].strip("'")
    # hostID = str(vm.summary.runtime.host).split(":")[1].strip("'")
    areaID = get_obj_id.id(vm.parent.parent)
    sysID = get_obj_id.id(vm.parent)
    hostID = get_obj_id.id(vm.summary.runtime.host)

    # VMSSTATE：虚拟机状态
    vmState = 'notRunning'
    if vmSummary.runtime.powerState == 'poweredOn':
        vmState = 'running'

    # VMWARE_TOOL： vmtools 状态
    vmTools = 'notInstalled'
    if vm.guest.toolsStatus == 'toolsOk':
        vmTools = 'installed'

    # VMSDISKNUM：虚拟机磁盘数量，用vmSummary.config.numVirtualDisks替代
    # vmDiskNum = 0
    # for device in vmConfig.hardware.device:
    #     if isinstance(device, vim.vm.device.VirtualDisk):
    #         vmDiskNum += 1

    # ISTEMPLATE：1 是模板，0 不是模板
    isTemplate = 0
    if vmConfig.template:
        isTemplate = 1

    # VMSTALL: 虚机磁盘总大小
    # stall = 0
    # for disk in vmConfig.hardware.device:
    #     if isinstance(disk, vim.vm.device.VirtualDisk):
    #         stall += disk.capacityInBytes
    stall = vm.storage.perDatastoreUsage[0].committed + \
            vm.storage.perDatastoreUsage[0].uncommitted

    # UPTIME: 虚拟机启动时间（这里是开机的时间）
    # datetime 类型的数据在 json 化的时候会默认转换成类似下面的格式
    # 'Sat Feb  4 00:00:00 2017'
    # 所以我们这里需要将 str 类型的时间串直接 json 化，然后在入库的时候再将其转换为 datetime类型
    bootTime = vmSummary.runtime.bootTime
    if bootTime:
        uptime = vmSummary.runtime.bootTime.strftime("%Y-%m-%d %H:%M:%S")
    else:
        uptime = ''

    # VMSTCHKTIME：虚机使用的存储信息的检查时间
    vmsChkTime = vm.storage.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    # 虚机信息字典
    # 'VMID': vmSummary.config.instanceUuid
    vminfo = {'VMID': get_obj_id.id(vm),
              'AREAID': areaID,
              'SYSID': sysID,
              'HOSTID': hostID,
              'VMSNAME': vm.name,
              'VMSFILE': vmConfig.datastoreUrl[0].url + "/" + vm.name + ".vmx",
              'VMSMEMORY': vmSummary.config.memorySizeMB,
              'UPTIME': uptime,
              'POWERSTATE': vmSummary.runtime.powerState,
              'OS': vmSummary.guest.guestFullName,
              'VMSSTATE': vmState,
              'MEMOVER': vmSummary.runtime.memoryOverhead,
              'VMSDNS_NAME': '',
              'VMWARE_TOOL': vmTools,
              'VMSDISKNUM': vmSummary.config.numVirtualDisks,
              'ISTEMPLATE': isTemplate,
              'VMSTCMT': vm.storage.perDatastoreUsage[0].committed,
              'VMSTUCMT': vm.storage.perDatastoreUsage[0].uncommitted,
              'VMSTALL': stall,
              'VMSTCHKTIME': vmsChkTime,
              'CHKTIME': '',
              'ID': '',
              'CLOUD': cloudid
              }

    return vminfo


def get_vm_vms(cloudid):
    """
    获取虚机以及它所使用的存储信息
    """

    global vmDict
    si_content = vcenter_instance_check.vc_instance_check(cloudid)

    datacenter = si_content.rootFolder.childEntity[0]
    datacenterName = datacenter.name

    container = si_content.rootFolder
    container_view = si_content.viewManager.CreateContainerView(
        container, [vim.VirtualMachine], True)
    # 获取所有的虚拟机
    vms = container_view.view

    vmsDict = {}
    for vm in vms:
        vmDict = vminfo(vm, cloudid)
        vmDict['DCID'] = get_obj_id.id(datacenter)
        vmDict['CLID'] = get_obj_id.id(vm.summary.runtime.host.parent)
        vmsDict[vm.name] = vmDict

    return vmsDict


if __name__ == "__main__":
    cloudid = 7
    print(get_vm_vms(cloudid))
