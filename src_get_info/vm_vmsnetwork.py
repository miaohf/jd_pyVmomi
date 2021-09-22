#!/usr/bin/env python3

"""
Written by jdreal.
Github:

Get the information about vcenter network.
"""

from pyVmomi import vim
from src_share import get_obj_id, vcenter_instance_check


def vmnetinfo(network, cloudid):
    # if network.name[:2] == "M_":
    #     sysmondata = 1
    # else:
    #     sysmondata = ''

    netDict = {'ID': get_obj_id.id(network),
               'NAME': network.name,
               'CHKTIME': '',
               'DESCRIPTION': '',
               'SYSMONDATA': '',
               'CLOUD': cloudid
               }

    return netDict


def get_vmnet_info(cloudid):
    si_content = vcenter_instance_check.vc_instance_check(cloudid)
    # 新增判断，当传入了错误的 cloudid 时，vc_instance_check() 返回的是一个包含错误信息的字典
    # 此时第 53 行给 datacenter 赋值的语句会报错
    if isinstance(si_content, dict):
        return si_content

    datacenter = si_content.rootFolder.childEntity[0]
    datecenterID = get_obj_id.id(datacenter)

    container = si_content.rootFolder
    # 获取所有虚拟机对象
    container_view = si_content.viewManager.CreateContainerView(
        container, [vim.Network], True)
    networks = container_view.view

    global netDict
    netDict = {}
    networkDict = {}
    for network in networks:
        netDict = vmnetinfo(network, cloudid)
        netDict['DATACENTER_ID'] = datecenterID
        networkDict['Network_' + network.name] = netDict

    return networkDict


if __name__ == "__main__":
    cloudid = 7
    print(get_vmnet_info(cloudid))
