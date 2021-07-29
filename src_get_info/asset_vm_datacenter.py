#!/usr/bin/env python3

"""
Written by jdreal.
Github:

Get the information about datacenter.
"""

from src_share import vcenter_instance_check, get_obj_id


def get_dc_info(cloudid):
    si_content = vcenter_instance_check.vc_instance_check(cloudid)

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
