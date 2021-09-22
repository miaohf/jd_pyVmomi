#!/usr/bin/env python3

"""
Written by jdreal.
Github:

Get the information about datacenter.
"""

from src_share import get_obj_id, vcenter_instance_check


def get_dc_info(cloudid):
    si_content = vcenter_instance_check.vc_instance_check(cloudid)
    # 新增判断，当传入了错误的 cloudid 时，vc_instance_check() 返回的是一个包含错误信息的字典
    # 此时第 53 行给 datacenter 赋值的语句会报错
    if isinstance(si_content, dict):
        return si_content

    datacenter = si_content.rootFolder.childEntity[0]

    dcDict = {'DCID': get_obj_id.id(datacenter),
              'DCNAME': datacenter.name,
              'DCTYPEID': '',
              'DCTYPENAME': '',
              'CHKTIME': '',
              'ID': '',
              'CLOUD': cloudid
              }

    return dcDict


if __name__ == "__main__":
    cloudid = 7
    print(get_dc_info(cloudid))
