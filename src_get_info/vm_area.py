#!/usr/bin/env python3

"""
Written by jdreal.
Github:

Get the information about vm 1st-level folders.
"""

from src_share import get_obj_id, vcenter_instance_check


def get_vm_area(cloudid):
    """
    打印最上层的虚拟机文件夹，对应 区域 的概念
    """

    si_content = vcenter_instance_check.vc_instance_check(cloudid)
    datacenter = si_content.rootFolder.childEntity[0]
    # datacenterName = datacenter.name

    vmFolder = datacenter.vmFolder.childEntity

    # dcDict = {}
    # vmFolderDict = {}
    # vmFolders = {}
    # for vmf in vmFolder:
    #     vmFolderDict['AREAID'] = get_obj_id.id(vmf)
    #     vmFolderDict['AREANAME'] = vmf.name
    #     vmFolderDict['CHKTIME'] = ''
    #     vmFolderDict['DESCRIPTION'] = ''
    #     vmFolderDict['ID'] = ''
    #     vmFolderDict['CLOUD'] = cloudid
    #     vmFolders['VMAREA_' + vmf.name] = vmFolderDict
    #     dcDict['DC_' + datacenterName] = vmFolders

    areas = []
    for vmf in vmFolder:
        areaDict = {}
        areaDict['AREAID'] = get_obj_id.id(vmf)
        areaDict['AREANAME'] = vmf.name
        areaDict['CHKTIME'] = ''
        areaDict['DESCRIPTION'] = ''
        areaDict['ID'] = ''
        areaDict['CLOUD'] = cloudid
        areas.append(areaDict)

    return areas


if __name__ == "__main__":
    cloudid = 7
    print(get_vm_area(cloudid))
