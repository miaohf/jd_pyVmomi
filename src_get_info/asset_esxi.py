#!/usr/bin/env python3

"""
Written by jdreal.
Github:

Get the information about ESXI.
"""

from src_share import get_obj_id, vcenter_instance_check
import math


def esxi_info(esxi, summary, hardware):
    # is connected ?
    """
    connected: Connected to the server. For ESX Server, this is always the setting.
    disconnected: The user has explicitly taken the host down. VirtualCenter does not expect to receive heartbeats from the host. The next time a heartbeat is received, the host is moved to the connected state again and an event is logged.
    notResponding: VirtualCenter is not receiving heartbeats from the server. The state automatically changes to connected once heartbeats are received again. This state is typically used to trigger an alarm on the host.
    """
    if summary.runtime.connectionState == 'connected':
        enabled = 1
    elif summary.runtime.connectionState == 'disconnected':
        enabled = 2
    else:
        enabled = 3

    # vmotion enabled ?
    if summary.config.vmotionEnabled == "true":
        vmotionenabled = 1
    else:
        vmotionenabled = 0

    esxiInfo = {'HOSTID': get_obj_id.id(esxi),
                'DCID': '',
                'CLID': '',
                'HOSTNAME': summary.config.name,
                'HOSTIP': summary.config.name,
                'ENABLED': enabled,
                'VMOTIONENABLED': vmotionenabled,
                'HOSTVENDOR': summary.hardware.vendor,
                'HOSTMODEL': summary.hardware.model,
                'CPUMODEL': summary.hardware.cpuModel,
                'CPUNUM': summary.hardware.numCpuPkgs,
                'CPUCORENUM': summary.hardware.numCpuCores,
                'CPUHZ': summary.hardware.cpuMhz,
                'CPUTHREADNUM': summary.hardware.numCpuThreads,
                'CPU_POWER_MGMT_POLICY': hardware.cpuPowerManagementInfo.currentPolicy,
                'CPU_POWER_MGMT_SUPPORT': hardware.cpuPowerManagementInfo.hardwareSupport,
                'MEMORY': math.ceil(
                    summary.hardware.memorySize / 1024 / 1024 / 1024),
                'BOOTTIME': summary.runtime.bootTime.strftime(
                    "%Y-%m-%d %H:%M:%S"),
                'DNSNAME': summary.config.name,
                'PRODUCTNAME': summary.config.product.name,
                'PRODUCTFULLNAME': summary.config.product.fullName,
                'PRODUCTVERSION': summary.config.product.version,
                'PRODUCTBUILD': summary.config.product.build,
                'PRODUCTVENDOR': summary.config.product.vendor,
                'PRODUCTOSTYPE': summary.config.product.osType,
                'PRODUCTAPITYPE': summary.config.product.apiType,
                'PRODUCTAPIVERSION': summary.config.product.apiVersion,
                'NICNUM': summary.hardware.numNics,
                'HBANUM': summary.hardware.numHBAs,
                'DASNODENAME': '',
                'POWERSTATE': summary.runtime.powerState,
                'CLIENTIPADDRESS': '',
                'MANAGEMENT_IP': esxi.config.network.vnic[0].spec.ip.ipAddress,
                'MMODE': 'no',
                'CHKTIME': '',
                'ID': '',
                'CLOUD': ''
                }

    return esxiInfo


def get_esxi_info(cloudid):
    si_content = vcenter_instance_check.vc_instance_check(cloudid)
    # vCenter_uuid = si_content.about.instanceUuid

    datacenter = si_content.rootFolder.childEntity[0]
    datacenterName = datacenter.name

    dcDict = {}
    esxiDict = {}
    clusterFolder = datacenter.hostFolder.childEntity
    for cluster in clusterFolder:
        for esxi in cluster.host:
            esxiSummary = esxi.summary
            esxiHardware = esxi.hardware
            esxiInfo = esxi_info(esxi, esxiSummary, esxiHardware)
            esxiInfo['DCID'] = get_obj_id.id(datacenter)
            esxiInfo['CLID'] = get_obj_id.id(cluster)
            esxiInfo['CLOUD'] = cloudid

            esxiDict['ESXI_' + esxiSummary.config.name] = esxiInfo

            # dcDict['DC_' + datacenterName] = esxiDict

    return esxiDict


if __name__ == "__main__":
    cloudid = 7
    print(get_esxi_info(cloudid))
