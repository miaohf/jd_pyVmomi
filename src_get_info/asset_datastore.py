#!/usr/bin/env python3

"""
Written by jdreal.
Github:

Get the information about vm and its datastore.
"""

from pyVmomi import vim
from src_share import get_obj_id, vcenter_instance_check


def dsinfo(ds, cloudid):
    dsSummary = ds.summary

    usedPercent = (
                              dsSummary.capacity - dsSummary.freeSpace) / dsSummary.capacity
    chkTime = ds.info.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    # 置备空间，Provisioned Space，就是已经分配出去了多少空间
    # 使用空间，Used Space，就是在 Provisioned Space 中已经确实被虚机或别的东西使用掉的空间
    # Uncommitted space 就是虚拟磁盘 Provisioned Space 与当前 Used Space（实际已使用空间）的差值
    # 计算公式：Provisioned = (Capacity - freeSpace) + uncommitted
    # 如果选用的是 thin 模式，Provisioned Space 和 Used Space 会不同；如果是厚置备，则两者完全一致或者相差不大
    # 另外，如果一个存储根本没有虚机来使用，那么它的uncommitted是None，则置备空间可以值为空值
    # 参考 https://is-cloud.blog.csdn.net/article/details/83062923
    # 参考 https://communities.vmware.com/t5/vSphere-Storage-Discussions/Difference-Between-Provision-and-Used-Space/td-p/1762364
    dsProvisioned = ''
    if dsSummary.uncommitted:
        dsProvisioned = (
                                    dsSummary.capacity - dsSummary.freeSpace) + dsSummary.uncommitted

    dsinfo = {'DSID': get_obj_id.id(ds),
              'DSNAME': ds.name,
              'CAPACITY': dsSummary.capacity,
              'FREESPACE': dsSummary.freeSpace,
              'USEAGEPERCENT': round(usedPercent, 2),
              'CAPACITYBZ': dsProvisioned,
              'DSTYPE': dsSummary.type,
              'DSURL': dsSummary.url,
              'IORMENABLED': (1 if ds.iormConfiguration.enabled else 0),
              'CHKTIME': chkTime,
              'ID': '',
              'CLOUD': cloudid}

    return dsinfo


def get_datastore_info(cloudid):
    si_content = vcenter_instance_check.vc_instance_check(cloudid)
    # 新增判断，当传入了错误的 cloudid 时，vc_instance_check() 返回的是一个包含错误信息的字典
    # 此时第 53 行给 datacenter 赋值的语句会报错
    if isinstance(si_content, dict):
        return si_content

    datacenter = si_content.rootFolder.childEntity[0]
    datacenterID = get_obj_id.id(datacenter)
    cluster = datacenter.hostFolder.childEntity[0]
    clusterID = get_obj_id.id(cluster)

    container = si_content.rootFolder
    container_view = si_content.viewManager.CreateContainerView(
        container, [vim.Datastore], True)
    # 获取所有的存储 datastore
    datastore = container_view.view

    global dsDict
    dsDict = {}
    for ds in datastore:
        dsdict = dsinfo(ds, cloudid)
        dsdict['DCID'] = datacenterID
        dsDict['DS_' + ds.name] = dsdict

    return dsDict


if __name__ == "__main__":
    cloudid = 7
    print(get_datastore_info(cloudid))
