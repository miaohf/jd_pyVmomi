#!/usr/bin/env python3

"""
Written by jdreal.
Github:

Get the information about resouce(cluster).
"""

from pyVmomi import vim
from src_share import get_obj_id, vcenter_instance_check


def get_cluster_info(cloudid):
    si_content = vcenter_instance_check.vc_instance_check(cloudid)
    # 新增判断，当传入了错误的 cloudid 时，vc_instance_check() 返回的是一个包含错误信息的字典
    # 此时第 53 行给 datacenter 赋值的语句会报错
    if isinstance(si_content, dict):
        return si_content

    datacenter = si_content.rootFolder.childEntity[0]

    container = si_content.rootFolder
    container_view = si_content.viewManager.CreateContainerView(
        container, [vim.ClusterComputeResource], True)
    # 获取所有的集群资源
    cluster = container_view.view

    clsRes = cluster[0]
    clsResSummary = clsRes.resourcePool.summary

    # 遍历集群内所有存储信息，计算总的存储空间
    capacity = 0
    for ds in clsRes.datastore:
        capacity += ds.summary.capacity

    clusResDict = {'CLID': get_obj_id.id(clsRes),
                   'DCID': get_obj_id.id(datacenter),
                   'CLNAME': clsRes.name,
                   'HAMODE': clsRes.configuration.dasConfig.enabled,
                   'DRSMODE': clsRes.configuration.drsConfig.enabled,
                   'ALLOCPU': clsResSummary.runtime.cpu.reservationUsed,
                   'ALLOVMCPU': clsResSummary.runtime.cpu.reservationUsedForVm,
                   'AVPOOLCPU': clsRes.summary.totalCpu,
                   'AVVMCPU': clsResSummary.runtime.cpu.overallUsage,
                   'ALLOMEM': clsResSummary.runtime.memory.reservationUsed,
                   'ALLOVMMEM': clsResSummary.runtime.memory.reservationUsedForVm,
                   'AVPOOLMEM': clsRes.summary.totalMemory,
                   'AVVMMEM': clsResSummary.runtime.memory.overallUsage,
                   'CURRCPU': clsResSummary.runtime.cpu.overallUsage,
                   'CURRMEM': clsResSummary.runtime.memory.overallUsage,
                   'OVERSTATUS': clsResSummary.runtime.overallStatus,
                   'CAPACITY': capacity,
                   'CHKTIME': '',
                   'ID': '',
                   'CLOUD': cloudid}

    return clusResDict


if __name__ == "__main__":
    cloudid = 7
    print(get_cluster_info(cloudid))
