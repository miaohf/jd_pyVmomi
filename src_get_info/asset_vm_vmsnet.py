#!/usr/bin/env python3

"""
Written by jdreal.
Github:

Get the information about vm's network devices.
"""

from pyVmomi import vim
from src_share import vcenter_instance_check, get_obj_id


def vmnetid(vm, devicename):
    for networkDevice in vm.network:
        if devicename != networkDevice.name:
            continue
        else:
            return get_obj_id.id(networkDevice)

    return -1


def vmnet_poweredon(vm, cloudid):
    """
    虚机的网卡信息，一个在 vm.network 里面
      - vm.network 是虚机所拥有的网卡的标签。例如一个虚机有三块网卡，标签分别是A,B,C，那么 vm.network 就有 A，B，C 三个对象；
        如果虚机有三块网卡，标签分别是A，B，A，那么 vm.network 就只有 A，B 两个对象
      - 要看虚机的 IP 等信息，查

    本段函数只处理处于开机状态的虚机
    """
    global vmNic, vmNetInfo
    vmNic = []
    count = 0
    vmNet = vm.guest.net
    for nicInfo in vmNet:
        ipcount = 0
        count += 1
        ipaddress = {}
        for ip in nicInfo.ipAddress:
            ipeach = {}
            ipaddress['IP_' + str(ipcount)] = ipeach
            ipeach['IP'] = ip
            global realipflag
            for ipreal in nicInfo.ipConfig.ipAddress:
                if ipreal.ipAddress != ip:
                    continue
                else:
                    if ipreal.prefixLength == 32:
                        realipflag = False
                    else:
                        realipflag = True

                # if ipreal.prefixLength == 64:
                #     ipV = 6
                # else:
                #     ipV = 4
            ipeach['REALIPFLAG'] = realipflag
            # ipeach['IPv'] = ipV
            ipcount += 1

        vmNetInfo = {'DEVICE_ID': (vmnetid(vm,
                                           nicInfo.network) if nicInfo.deviceConfigId != -1 else ''),
                     'MAC_ADDRESS': nicInfo.macAddress,
                     'IS_CONNECTED': (1 if nicInfo.connected else 0),
                     'NETWORK_NAME': (
                         nicInfo.network if nicInfo.deviceConfigId != -1 else ''),
                     'IPADDRESS': ipaddress,
                     'SUBNETWORKID': '',
                     # 'REALIPFLAG': '',
                     }

        # vmNic['Nic_' + str(count)] = vmNetInfo
        vmNic.append(vmNetInfo)
    return vmNic


def vmnet_poweredoff(vm):
    global vmNet, vmDevice
    vmNet = []
    vmDevice = {}
    # count = 0

    for vmnet in vm.network:
        vmDevice = {
            'DEVICE_ID': (get_obj_id.id(vmnet) if len(vm.network) != 0 else ''),
            'MAC_ADDRESS': '',
            'IS_CONNECTED': '',
            'NETWORK_NAME': (vmnet.name if len(vm.network) != 0 else ''),
            'IPADDRESS': '',
            'SUBNETWORKID': '',
            'REALIPFLAG': '',
        }
        vmNet.append(vmDevice)
        # count += 1
        # vmNet['Nic_' + str(count)] = vmDevice

    return vmNet


def get_vmnet_info(cloudid):
    si_content = vcenter_instance_check.vc_instance_check(cloudid)

    # datacenter = si_content.rootFolder.childEntity[0]

    container = si_content.rootFolder
    # 获取所有虚拟机对象
    container_view = si_content.viewManager.CreateContainerView(
        container, [vim.VirtualMachine], True)
    vms = container_view.view

    global vmNetInfoDict
    vmNetInfoDict = {}

    # 根据虚机的电源状况，分别构建字典
    # for vm in vms:
    #     if vm.runtime.powerState == 'poweredOn':
    #         vmNetInfoDict['VM_' + vm.name] = vmnet_poweredon(vm, cloudid)
    #         vmNetInfoDict['VM_' + vm.name]['VMID'] = get_obj_id.id(vm)
    #         vmNetInfoDict['VM_' + vm.name]['CLOUD'] = cloudid
    #         vmNetInfoDict['VM_' + vm.name]['CHKTIME'] = ''
    #     else:
    #         vmNetInfoDict['VM_' + vm.name] = vmnet_poweredoff(vm)
    #         vmNetInfoDict['VM_' + vm.name]['VMID'] = get_obj_id.id(vm)
    #         vmNetInfoDict['VM_' + vm.name]['CLOUD'] = cloudid
    #         vmNetInfoDict['VM_' + vm.name]['CHKTIME'] = ''

    for vm in vms:
        if vm.runtime.powerState == 'poweredOn':
            vmNetInfoDict['VM_' + vm.name] = {}
            vmNetInfoDict['VM_' + vm.name]['VMID'] = get_obj_id.id(vm)
            vmNetInfoDict['VM_' + vm.name]['CLOUD'] = cloudid
            vmNetInfoDict['VM_' + vm.name]['CHKTIME'] = ''
            vmNetInfoDict['VM_' + vm.name]['Nic'] = vmnet_poweredon(vm, cloudid)
        else:
            vmNetInfoDict['VM_' + vm.name] = {}
            vmNetInfoDict['VM_' + vm.name]['VMID'] = get_obj_id.id(vm)
            vmNetInfoDict['VM_' + vm.name]['CLOUD'] = cloudid
            vmNetInfoDict['VM_' + vm.name]['CHKTIME'] = ''
            vmNetInfoDict['VM_' + vm.name]['Nic'] = vmnet_poweredoff(vm)

    return vmNetInfoDict


if __name__ == "__main__":
    cloudid = 7
    print(get_vmnet_info(cloudid))
