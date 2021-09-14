#!/usr/bin/env python3

"""
Written by jdreal.
Github: 

Some
"""

from pyVmomi import vim
from src_share import get_objInfo, logger, get_obj_id, task_check, response
import time
import string
import random


class VirtualMachine:
    def __init__(self, name, pfolder, cloudid):
        self.__name = name
        self.__pfolder = pfolder
        self.__cloudid = cloudid

    def vm_exist_check(self):
        """
        检查虚机是否存在，需要给出虚机的名字以及虚机的父文件夹（不同文件夹下虚机名字可以相同）。
        :return:
        """
        log = logger.Logger("vCenter_vm_operations")

        pfolderObj = get_objInfo.get_obj(self.__cloudid, [vim.Folder],
                                         self.__pfolder)
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        for vminstance in pfolderObj.childEntity:
            if not isinstance(vminstance, vim.VirtualMachine):
                continue
            else:
                if vminstance.name != self.__name:
                    continue
                else:
                    msg = ("虚机 {} 位于文件夹 {} 下，其 ID 为 {}，".format(self.__name,
                                                                self.__pfolder,
                                                                get_obj_id.id(
                                                                    vminstance)))
                    log.info(msg)
                    code = 0
                    return response.return_info(code, msg)

        msg = (
            "文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder, self.__name))
        log.error(msg)
        code = 1
        return response.return_info(code, msg)

    def get_vm_obj(self):
        """
        根据用户给出的虚机名字和父文件夹名字，查找正确的虚拟机，返回该虚拟机对象。
        此函数与上面的 vm_exist_check 函数一模一样，返回不同而已。上面的用来给API调用，
        这个函数用来给 VirtualMachine 类实例调用。后面诸如克隆、重命名等函数会调用本函数
        来查找虚机对象是否存在。

        返回值：
        vm：返回虚拟机对象
        pfolderObj：返回父文件夹对象
        """
        pfolderObj = get_objInfo.get_obj(self.__cloudid, [vim.Folder],
                                         self.__pfolder)
        if pfolderObj is None:
            return None, None

        for vminstance in pfolderObj.childEntity:
            if not isinstance(vminstance, vim.VirtualMachine):
                continue
            else:
                if vminstance.name != self.__name:
                    continue
                else:
                    return vminstance, pfolderObj

        return None, pfolderObj

    def vm_clone(self, newvm, newvmpfolder, newvmhost='', newvmdatastore=''):
        """
        此函数用来从模板克隆一台新的虚拟机。
        self 即模板本身
        :param newvm: 新虚机的名字
        :param newvmpfolder: 新虚机所在的文件夹
        :param newvmhost: 新虚机所在主机，可以为空（和模板一致）
        :param newvmdatastore: 新虚机所在存储，可以为空（和模板一致）
        """
        log = logger.Logger("vCenter_vm_operations")

        # 可以不指定模板虚机的父文件夹。这要求模板名字要唯一且准确无误
        if self.__pfolder is None:
            templateToClone = get_objInfo.get_obj(self.__cloudid,
                                                  [vim.VirtualMachine],
                                                  self.__name)
        else:
            templateToClone, pfolderObj = self.get_vm_obj()
            if pfolderObj is None:
                msg = ("指定的模板的父文件夹 {} 不存在。".format(self.__pfolder))
                log.error(msg)
                code = 1
                return response.return_info(code, msg)

            if templateToClone is None:
                msg = ("指定的模板 {} 不存在。".format(self.__name))
                log.error(msg)
                code = 1
                return response.return_info(code, msg)

        if not newvm:
            msg = "未指定新虚机名字。"
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        # 检查新虚机的目录是否存在
        folderToClone = get_objInfo.get_obj(self.__cloudid, [vim.Folder],
                                            newvmpfolder)
        if not folderToClone:
            msg = ("指定的新虚机的父文件夹 {} 不存在。".format(newvmpfolder))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        # vm's name
        vmNameToClone = newvm

        # 如果没有指定主机，则默认和模板所使用的主机一致
        if not newvmhost:
            hostToClone = templateToClone.summary.runtime.host
        else:
            hostToClone = get_objInfo.get_obj(self.__cloudid,
                                              [vim.HostSystem],
                                              newvmhost)
        if not hostToClone:
            msg = ("指定的主机 {} 不存在。".format(newvmhost))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        # 如果没有指定存储，则默认和模板所使用的存储一致
        # 如果指定了存储，则先检查指定的存储是否属于主机hostToClone
        if not newvmdatastore:
            # 创建模板时，模板有且仅有一个存储
            datastoreToClone = templateToClone.datastore[0]
        else:
            datastoreToClone = get_objInfo.get_obj(self.__cloudid,
                                                   [vim.Datastore],
                                                   newvmdatastore)
        if datastoreToClone is None:
            msg = ("指定的存储 {} 不存在。".format(newvmdatastore))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if datastoreToClone not in hostToClone.datastore:
            msg = (
                "指定的存储 {} 不属于主机 {}。".format(datastoreToClone.name,
                                            hostToClone.name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        # set resource pool，vc里只有一个资源池 Resources
        cloneResource_pool = get_objInfo.get_obj(self.__cloudid,
                                                 [vim.ResourcePool],
                                                 "Resources")

        # 开始准备克隆虚机所需的 spec
        cloneRelocateSpec = vim.vm.RelocateSpec()
        cloneRelocateSpec.datastore = datastoreToClone
        cloneRelocateSpec.pool = cloneResource_pool
        cloneRelocateSpec.host = hostToClone

        cloneSpec = vim.vm.CloneSpec()
        cloneSpec.location = cloneRelocateSpec
        cloneSpec.powerOn = True

        try:
            task = templateToClone.Clone(folderToClone, vmNameToClone,
                                         cloneSpec)
            o, m = task_check.task_check(task)
            if o == 'OK':
                msg = ("新虚机 {} 克隆成功。".format(newvm))
                log.info(msg)
                code = 0
                return response.return_info(code, msg)
            else:
                log.error(m)
                code = 1
                return response.return_info(code, m)

        except vim.fault.RuntimeFault as e:
            msg = ("新虚机 {} 克隆失败：{}。".format(newvm, e.msg))
            log.info(msg)
            code = 1
            return response.return_info(code, msg)

    def vm_clone_with_ip(self, newvm, newvmpfolder, newip, newvmhost='',
                         newvmdatastore=''):
        """
        此函数用来从模板克隆一台新的虚拟机。
        self 即模板本身
        :param newvm: 新虚机的名字，注意不能包含下划线 "_" 或者空格 " " 或者圆点符 "."
        :param newvmpfolder: 新虚机所在的文件夹
        :param newip: 新虚拟机要配置的 IP 列表（可以参考下方 vm_configure_ipaddress（） ）
        :param newvmhost: 新虚机所在主机，可以为空（和模板一致）
        :param newvmdatastore: 新虚机所在存储，可以为空（和模板一致）
        """
        log = logger.Logger("vCenter_vm_operations")

        # 可以不指定模板虚机的父文件夹。这要求模板名字要唯一且准确无误
        if self.__pfolder is None:
            templateToClone = get_objInfo.get_obj(self.__cloudid,
                                                  [vim.VirtualMachine],
                                                  self.__name)
        else:
            templateToClone, pfolderObj = self.get_vm_obj()
            if pfolderObj is None:
                msg = ("指定的模板的父文件夹 {} 不存在。".format(self.__pfolder))
                log.error(msg)
                code = 1
                return response.return_info(code, msg)

            if templateToClone is None:
                msg = ("指定的模板 {} 不存在。".format(self.__name))
                log.error(msg)
                code = 1
                return response.return_info(code, msg)

        if not newvm:
            msg = "未指定新虚机名字。"
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        # 检查新虚机的目录是否存在
        folderToClone = get_objInfo.get_obj(self.__cloudid, [vim.Folder],
                                            newvmpfolder)
        if not folderToClone:
            msg = ("指定的新虚机的父文件夹 {} 不存在。".format(newvmpfolder))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        # vm's name
        vmNameToClone = newvm

        # 如果没有指定主机，则默认和模板所使用的主机一致
        if not newvmhost:
            hostToClone = templateToClone.summary.runtime.host
        else:
            hostToClone = get_objInfo.get_obj(self.__cloudid,
                                              [vim.HostSystem],
                                              newvmhost)
        if not hostToClone:
            msg = ("指定的主机 {} 不存在。".format(newvmhost))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        # 如果没有指定存储，则默认和模板所使用的存储一致
        # 如果指定了存储，则先检查指定的存储是否属于主机hostToClone
        if not newvmdatastore:
            # 创建模板时，模板有且仅有一个存储
            datastoreToClone = templateToClone.datastore[0]
        else:
            datastoreToClone = get_objInfo.get_obj(self.__cloudid,
                                                   [vim.Datastore],
                                                   newvmdatastore)
        if datastoreToClone is None:
            msg = ("指定的存储 {} 不存在。".format(newvmdatastore))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if datastoreToClone not in hostToClone.datastore:
            msg = (
                "指定的存储 {} 不属于主机 {}。".format(datastoreToClone.name,
                                            hostToClone.name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        # set resource pool，vc里只有一个资源池 Resources
        cloneResource_pool = get_objInfo.get_obj(self.__cloudid,
                                                 [vim.ResourcePool],
                                                 "Resources")

        if len(newip) == 0:
            msg = ("未指定新虚机的 IP 列表。".format(newvmhost))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        # 新虚机所在的存储、主机、资源次等信息的 spec
        cloneRelocateSpec = vim.vm.RelocateSpec()
        cloneRelocateSpec.datastore = datastoreToClone
        cloneRelocateSpec.pool = cloneResource_pool
        cloneRelocateSpec.host = hostToClone

        # 新虚机 ip 信息的 spec
        # 为每一块网卡配置一个 IP
        global nicSettingMap
        nicSettingMap = []
        for ip in newip:
            # 在我的环境内，第一个 IP 地址的掩码会配置成 20
            if newip.index(ip) == 0:
                subnetMask = '255.255.240.0'
            else:
                subnetMask = '255.255.255.0'

            adapterMap = vim.vm.customization.AdapterMapping()
            adapterMap.adapter = vim.vm.customization.IPSettings()
            adapterMap.adapter.ip = vim.vm.customization.FixedIp()
            adapterMap.adapter.ip.ipAddress = ip
            adapterMap.adapter.subnetMask = subnetMask
            # 在我的环境内，第三个 IP 需要配置网关
            if newip.index(ip) == 2:
                gateway = ".".join(str(ip).split(".")[:3]) + ".1"
                adapterMap.adapter.gateway = gateway
            nicSettingMap.append(adapterMap)

        globalIP = vim.vm.customization.GlobalIPSettings()
        ident = vim.vm.customization.LinuxPrep()
        ident.hostName = vim.vm.customization.FixedName()
        # 主机名设置为 'vm-' + cloudid（只有一位的前面补一个0） + '-' + 5 位随机字符串（不能全部是数字）
        cloudID = str(self.__cloudid)
        if len(cloudID) == 1:
            cloudID = '0' + cloudID

        while True:
            randomStr = ''.join(
                random.choice(string.ascii_lowercase + string.digits) for _ in
                range(5))
            if not randomStr.isdigit():
                break

        ident.hostName.name = "vm-" + cloudID + '-' + randomStr

        # 设置自定义配置文件
        cloneCustomSpec = vim.vm.customization.Specification()
        cloneCustomSpec.nicSettingMap = nicSettingMap
        cloneCustomSpec.globalIPSettings = globalIP
        cloneCustomSpec.identity = ident

        # clone 所需的 spec
        cloneSpec = vim.vm.CloneSpec()
        cloneSpec.location = cloneRelocateSpec
        cloneSpec.customization = cloneCustomSpec
        cloneSpec.powerOn = True

        try:
            task = templateToClone.Clone(folderToClone, vmNameToClone,
                                         cloneSpec)
            o, m = task_check.task_check(task)
            if o == 'OK':
                msg = ("新虚机 {} 克隆成功。".format(newvm))
                log.info(msg)
                code = 0
                return response.return_info(code, msg)
            else:
                log.error(m)
                code = 1
                return response.return_info(code, m)

        except vim.fault.RuntimeFault as e:
            msg = ("新虚机 {} 克隆失败：{}。".format(newvm, e.msg))
            log.info(msg)
            code = 1
            return response.return_info(code, msg)

    def vm_delete(self):
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity.runtime.powerState == "poweredOn":
            msg = ("虚拟机 {} 当前处于开机状态，无法删除。".format(self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        try:
            task = vmEntity.Destroy_Task()
            o, m = task_check.task_check(task)
            if o == 'OK':
                msg = ("虚机 {} 已被成功删除。".format(self.__name))
                log.info(msg)
                code = 0
                return response.return_info(code, msg)
            else:
                log.error(m)
                code = 1
                return response.return_info(code, msg)
        except vim.fault.VimFault as e:
            msg = ("虚机 {} 删除失败。".format(self.__name)) + e
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

    def vm_rename(self, newname):
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        try:
            vmEntity.Rename(newname)
            msg = ("虚机 {} 成功重命名为 {}。".format(self.__name, newname))
            log.info(msg)
            code = 0
            return response.return_info(code, msg)
        except vim.fault.VimFault as e:
            msg = ("虚机 {} 重命名失败。".format(self.__name)) + e
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

    def vm_poweroff(self):
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity.runtime.powerState == "poweredOff":
            msg = ("虚拟机 {} 当前已经处于关机状态，无法关闭电源。".format(self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        try:
            task = vmEntity.PowerOff()
            o, m = task_check.task_check(task)
            if o == 'OK':
                msg = ("虚机 {} 已成功关闭电源。".format(self.__name))
                log.info(msg)
                code = 0
                return response.return_info(code, msg)
            else:
                log.error(m)
                code = 1
                return response.return_info(code, m)
        except vim.fault.VimFault as e:
            msg = ("虚机 {} 关闭电源失败。".format(self.__name)) + e
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

    def vm_poweron(self):
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if not pfolderObj:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity.runtime.powerState == "poweredOn":
            msg = ("虚拟机 {} 当前已经处于开机状态，无法打开电源。".format(self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        try:
            task = vmEntity.PowerOn()
            o, m = task_check.task_check(task)
            if o == 'OK':
                msg = ("虚机 {} 已成功打开电源。".format(self.__name))
                log.info(msg)
                return 'OK'
            else:
                log.error(m)
                code = 1
                return response.return_info(code, m)
        except vim.fault.VimFault as e:
            msg = ("虚机 {} 打开电源失败。".format(self.__name)) + e
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

    def vm_reboot(self):
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        try:
            vmEntity.RebootGuest()
            msg = ("虚机 {} 已成功重启。".format(self.__name))
            log.info(msg)
            code = 0
            return response.return_info(code, msg)
        except vim.fault.InvalidPowerState as e:
            msg = ("虚机 {} 重启失败。".format(self.__name)) + e.msg
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

    def vm_snapshot_create(self):
        """
        为虚机打快照，快照名字和描述根据当时的时间来定义。
        """
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        localTime = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime())

        snapshotName = self.__name + "_" + localTime
        snapshotDescription = "snapshot for vm '" + self.__name + "' " + \
                              localTime

        try:
            task = vmEntity.CreateSnapshot(name=snapshotName,
                                           description=snapshotDescription,
                                           memory=False,
                                           quiesce=False)
            o, m = task_check.task_check(task)
            if o == 'OK':
                msg = ("成功为虚机 {} 新建快照 {}。".format(self.__name, snapshotName))
                log.info(msg)
                code = 0
                return response.return_info(code, msg)
            else:
                log.error(m)
                code = 1
                return response.return_info(code, msg)
        except vim.fault.SnapshotFault as e:
            msg = ("虚机 {} 快照新建失败。".format(self.__name)) + e.msg
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

    def vm_snapshot_delete(self, snapshot_name):
        """
        先通过 vm_snapshot_list() 获取该虚机的快照列表
        然后根据参数 snapshot_name 去查找快照对象
        最后调用 RemoveSnapshot_Task 删除快照
        :param snapshot_name: 要删除的快照名
        """
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity.snapshot is None:
            msg = ("虚机 {} 不存在任何快照。".format(self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        # get all snapshots that belong to the vm
        rootSnapshot = vmEntity.snapshot.rootSnapshotList
        snapshotList = vm_snapshot_list(rootSnapshot)

        snapshotDel = None
        for snapshot in snapshotList:
            if snapshot_name == snapshot["Name"]:
                snapshotDel = snapshot["SnapshotObj"]

        if snapshotDel is None:
            msg = ("虚机 {} 下找不到快照 {}。".format(self.__name, snapshot_name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        try:
            task = snapshotDel.RemoveSnapshot_Task(removeChildren=False)
            o, m = task_check.task_check(task)
            if o == 'OK':
                msg = ("成功删除虚机 {} 的快照 {}。".format(self.__name, snapshot_name))
                log.info(msg)
                code = 0
                return response.return_info(code, msg)
            else:
                log.error(m)
                code = 1
                return response.return_info(code, m)
        except vim.fault.SnapshotFault as e:
            msg = ("虚机 {} 的快照 {} 删除失败。".format(self.__name,
                                               snapshot_name)) + e.msg
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

    def vm_snapshot_revert(self, snapshot_name):
        """
        先通过 vm_snapshot_list() 获取该虚机的快照列表
        然后根据参数 snapshot_name 去查找快照对象
        最后调用 RevertToSnapshot_Task 恢复快照
        注意：由于打的快照都没保存内存状态，所以恢复后虚机会处于关机状态
        :param snapshot_name: 要恢复到的快照的名字
        """
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity.snapshot is None:
            msg = ("虚机 {} 不存在任何快照。".format(self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        rootSnapshot = vmEntity.snapshot.rootSnapshotList
        snapshotList = vm_snapshot_list(rootSnapshot)

        snapshotRevert = None
        for snapshot in snapshotList:
            if snapshot_name == snapshot["Name"]:
                snapshotRevert = snapshot["SnapshotObj"]

        if snapshotRevert is None:
            msg = ("虚机 {} 下找不到快照 {}。".format(self.__name, snapshot_name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        try:
            task = snapshotRevert.RevertToSnapshot_Task()
            o, m = task_check.task_check(task)
            if o == 'OK':
                msg = ("成功将虚机 {} 恢复到快照 {}。".format(self.__name, snapshot_name))
                log.info(msg)
                code = 0
                return response.return_info(code, msg)
            else:
                log.error(m)
                code = 1
                return response.return_info(code, m)
        except vim.fault.SnapshotFault as e:
            msg = ("虚机 {} 恢复到快照 {} 失败。".format(self.__name,
                                               snapshot_name)) + e.msg
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

    def vm_snapshot_delete_all(self):
        """
        delete all the snapshots of a VM
        """
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity.snapshot is None:
            msg = ("虚机 {} 不存在任何快照。".format(self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        try:
            task = vmEntity.RemoveAllSnapshots_Task()
            o, m = task_check.task_check(task)
            if o == 'OK':
                msg = ("成功将虚机 {} 的所有快照删除。".format(self.__name))
                log.info(msg)
                code = 0
                return response.return_info(code, msg)
            else:
                log.error(m)
                code = 1
                return response.return_info(code, m)
        except vim.fault.SnapshotFault as e:
            msg = ("虚机 {} 的所有快照删除失败。".format(self.__name)) + e.msg
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

    def vm_reconfigure_mem(self, newmemsize):
        newmemsize = int(newmemsize)
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if not newmemsize:
            msg = ("未指定新的内存大小(G)，无法重新配置虚机 {}。".format(self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        currentMem = vmEntity.summary.config.memorySizeMB
        if currentMem / 1024 == newmemsize:
            msg = ("虚机 {} 当前内存大小等于新指定的内存大小。".format(self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity.summary.runtime.powerState == "poweredOn":
            msg = ("虚机 {} 当前处于开机状态，无法重新配置内存大小。".format(self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        spec = vim.vm.ConfigSpec()
        spec.memoryMB = newmemsize * 1024

        try:
            task = vmEntity.ReconfigVM_Task(spec=spec)
            o, m = task_check.task_check(task)
            if o == 'OK':
                msg = ("成功将虚机 {} 的内存调整为 {} GB。".format(self.__name, newmemsize))
                log.info(msg)
                code = 0
                return response.return_info(code, msg)
            else:
                log.error(m)
                code = 1
                return response.return_info(code, m)

        except vim.fault.VmConfigFault as e:
            msg = ("调整虚机 {} 内存失败。".format(self.__name)) + e.msg
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

    def vm_reconfigure_cpu(self, newcpunum):
        newcpunum = int(newcpunum)
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if not newcpunum:
            msg = ("未指定新的CPU数量，无法重新配置虚机 {}。".format(self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        currentCpuNum = vmEntity.summary.config.numCpu
        if currentCpuNum == newcpunum:
            msg = ("虚机 {} 当前内存大小等于新指定的CPU数量。".format(self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity.summary.runtime.powerState == "poweredOn":
            msg = ("虚机 {} 当前处于开机状态，无法重新配置CPU数量。".format(self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        spec = vim.vm.ConfigSpec()
        spec.numCPUs = newcpunum

        try:
            task = vmEntity.ReconfigVM_Task(spec=spec)
            o, m = task_check.task_check(task)
            if o == 'OK':
                msg = ("成功将虚机 {} 的CPU数量调整为 {} 。".format(self.__name, newcpunum))
                log.info(msg)
                code = 0
                return response.return_info(code, msg)
            else:
                log.error(m)
                code = 1
                return response.return_info(code, m)

        except vim.fault.VmConfigFault as e:
            msg = ("调整虚机 {} CPU数量失败。".format(self.__name)) + e.msg
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

    def vm_reconfigure_nic_add(self, newnicname):
        """
        为虚机添加一块网卡，类型写死为 Vmxnet3
        :param newnicname: 要添加的网卡的标签名
        """
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if not newnicname:
            msg = "未指定要添加的网卡名。"
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        newNicObj = get_objInfo.get_obj(self.__cloudid, [vim.Network],
                                        newnicname)
        if newNicObj is None:
            msg = ("指定的网卡 {} 不存在。".format(newnicname))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        spec = vim.vm.ConfigSpec()
        nicChanges = []

        nicSpec = vim.vm.device.VirtualDeviceSpec()
        nicSpec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add

        nicSpec.device = vim.vm.device.VirtualVmxnet3()
        nicSpec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        nicSpec.device.connectable.startConnected = True
        nicSpec.device.connectable.allowGuestControl = True
        nicSpec.device.connectable.connected = True
        nicSpec.device.connectable.status = 'untried'
        # MAC address assigned by VirtualCenter.
        nicSpec.device.addressType = 'assigned'

        if isinstance(newNicObj, vim.OpaqueNetwork):
            nicSpec.device.backing = \
                vim.vm.device.VirtualEthernetCard.OpaqueNetworkBackingInfo()
            nicSpec.device.backing.opaqueNetworkType = \
                newNicObj.summary.opaqueNetworkType
            nicSpec.device.backing.opaqueNetworkId = \
                newNicObj.summary.opaqueNetworkId
        else:
            nicSpec.device.backing = \
                vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
            nicSpec.device.backing.useAutoDetect = False
            nicSpec.device.backing.deviceName = newnicname

        nicChanges.append(nicSpec)
        spec.deviceChange = nicChanges

        try:
            task = vmEntity.ReconfigVM_Task(spec=spec)
            o, m = task_check.task_check(task)
            if o == 'OK':
                msg = ("成功为虚机 {} 添加了一块网卡 {} 。".format(self.__name, newnicname))
                log.info(msg)
                code = 0
                return response.return_info(code, msg)
            else:
                log.error(m)
                code = 1
                return response.return_info(code, m)
        except vim.fault.VmConfigFault as e:
            msg = ("虚机 {} 添加网卡 {} 失败。".format(self.__name, newnicname)) + e.msg
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

    def vm_reconfigure_nic_remove(self, nicnumber):
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if not nicnumber:
            msg = "未指定要删除的网卡序号。"
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        global diskPrefixLabel
        for dev in vmEntity.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualEthernetCard):
                # dev.deviceInfo.label 要么是 '网络适配器 N'，要么是'Network adapter N'
                # 所以判断字符串 dev.deviceInfo.label 第一个字符即可
                # 如果 label 内含有中文（在Unicode编码中4E00-9FFF为中文字符编码区）
                if u'\u4e00' <= dev.deviceInfo.label[0] <= u'\u9fff':
                    diskPrefixLabel = '网络适配器 '
                    break
                else:
                    diskPrefixLabel = 'Network adapter '
                    break

        nicLabel = diskPrefixLabel + str(nicnumber)
        nicDeviceToRemove = None
        for dev in vmEntity.config.hardware.device:
            # 用网卡的 label 来唯一标识网卡
            if isinstance(dev, vim.vm.device.VirtualEthernetCard) \
                    and dev.deviceInfo.label == nicLabel:
                nicDeviceToRemove = dev

        if not nicDeviceToRemove:
            msg = ("虚机 {} 没有网卡序号为 {} 的网卡。".format(self.__name, nicnumber))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        # 配置 vim.vm.device.VirtualDeviceSpec()，将 operation 设置为 remove
        nicSpec = vim.vm.device.VirtualDeviceSpec()
        nicSpec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
        nicSpec.device = nicDeviceToRemove

        spec = vim.vm.ConfigSpec()
        spec.deviceChange = [nicSpec]

        try:
            task = vmEntity.ReconfigVM_Task(spec=spec)
            o, m = task_check.task_check(task)
            if o == 'OK':
                msg = ("成功为虚机 {} 第 {} 块网卡。".format(self.__name, nicnumber))
                log.info(msg)
                code = 0
                return response.return_info(code, msg)
            else:
                log.error(m)
                code = 1
                return response.return_info(code, m)

        except vim.fault.VmConfigFault as e:
            msg = ("虚机 {} 删除第 {} 块网卡失败。".format(self.__name, nicnumber)) + e.msg
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

    def vm_reconfigure_disk_add(self, disksize):
        """
        :param disksize: 新增磁盘的大小(GB)
        新增的磁盘默认为精简置备
        """
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if not disksize:
            msg = "未指定新增磁盘大小。"
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        spec = vim.vm.ConfigSpec()
        diskSizeInKB = int(disksize) * 1024 * 1024
        # unitNumber 和 controllerKey 一定要指定。另外一个controllerKey 最多可以挂16块
        # 硬盘，再多就需要新增一个 controllerKey。
        # 由于我们环境内一般一台虚机最多就4,5块磁盘，故这里只做一个简单的判断。

        unitNumber = 0
        for dev in vmEntity.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualDisk):
                unitNumber += 1
                if unitNumber >= 16:
                    msg = "虚机 {} 当前已有16块盘，无法继续新增磁盘。".format(self.__name)
                    log.error(msg)
                    return 'Failed'
            # controllerKey 等于最后一块盘的 controllerKey
            controllerKey = dev.controllerKey

        diskSpec = vim.vm.device.VirtualDeviceSpec()
        diskSpec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        diskSpec.fileOperation = "create"
        diskSpec.device = vim.vm.device.VirtualDisk()
        diskSpec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
        diskSpec.device.backing.thinProvisioned = True
        diskSpec.device.backing.diskMode = 'persistent'
        diskSpec.device.capacityInKB = diskSizeInKB
        diskSpec.device.unitNumber = unitNumber
        diskSpec.device.controllerKey = controllerKey
        devChanges = [diskSpec]
        spec.deviceChange = devChanges

        try:
            task = vmEntity.ReconfigVM_Task(spec=spec)
            o, m = task_check.task_check(task)
            if o == 'OK':
                msg = ("成功为虚机 {} 新增了一块 {}GB 的磁盘。".format(self.__name, disksize))
                log.info(msg)
                code = 0
                return response.return_info(code, msg)
            else:
                log.error(m)
                code = 1
                return response.return_info(code, m)

        except vim.fault.VmConfigFault as e:
            msg = ("虚机 {} 新增磁盘失败。".format(self.__name)) + e.msg
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

    def vm_reconfigure_disk_remove(self, disknumber):
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if not disknumber:
            msg = "未指定新增磁盘序号。"
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        global diskPrefixLabel
        diskPrefixLabel = None
        for dev in vmEntity.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualDisk):
                # dev.deviceInfo.label 要么是 '硬盘 N'，要么是'Hard disk N'
                # 所以判断字符串 dev.deviceInfo.label 第一个字符即可
                # 如果 label 内含有中文（在Unicode编码中4E00-9FFF为中文字符编码区）
                if u'\u4e00' <= dev.deviceInfo.label[0] <= u'\u9fff':
                    diskPrefixLabel = '硬盘 '
                    break
                else:
                    diskPrefixLabel = 'Hard disk '
                    break

        if not diskPrefixLabel:
            msg = "无法找到的磁盘标签前缀。"
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        diskLabel = diskPrefixLabel + str(disknumber)
        diskDevice = None
        for dev in vmEntity.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualDisk) and \
                    dev.deviceInfo.label == diskLabel:
                diskDevice = dev
        if not diskDevice:
            msg = "虚机 {} 下找不到磁盘序号为 {} 的磁盘。".format(self.__name, disknumber)
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        diskSpec = vim.vm.device.VirtualDeviceSpec()
        diskSpec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
        diskSpec.device = diskDevice

        spec = vim.vm.ConfigSpec()
        spec.deviceChange = [diskSpec]

        try:
            task = vmEntity.ReconfigVM_Task(spec=spec)
            o, m = task_check.task_check(task)
            if o == 'OK':
                msg = ("成功为虚机 {} 删除了第 {} 块磁盘。".format(self.__name, disknumber))
                log.info(msg)
                code = 0
                return response.return_info(code, msg)
            else:
                log.error(m)
                code = 1
                return response.return_info(code, m)

        except vim.fault.VmConfigFault as e:
            msg = ("虚机 {} 删除第 {} 块磁盘失败。".format(self.__name,
                                                disknumber)) + e.msg
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

    def vm_configure_ipaddress(self, newip):
        """
        为虚机配置 IP 使用  CustomizeVM_Task 方法。在不指定网卡 MAC 的情况下，该方法会
        按照网卡序号的顺序（即 Network Adapter 1/2/3，也即 vc 上看到的顺序）为网卡配置IP。
        在我们的环境内，每台虚机默认有三块网卡，所以 newip 里会按约定好的顺序写入IP地址。
        另外，一个 IP 会对应一个网络适配器，我们需要配置好所有网络适配器的参数。
        :param newip: 一个列表，包含三个IP。（IP 个数根据自身环境情况自定义）
        """
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if len(newip) == 0:
            msg = "未指定 IP 地址。"
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        # 为每一块网卡配置一个 IP
        global nicSettingMap
        nicSettingMap = []
        for ip in newip:
            # 在我的环境内，第一个 IP 地址的掩码会配置成 20
            if newip.index(ip) == 0:
                subnetMask = '255.255.240.0'
            else:
                subnetMask = '255.255.255.0'

            adapterMap = vim.vm.customization.AdapterMapping()
            adapterMap.adapter = vim.vm.customization.IPSettings()
            adapterMap.adapter.ip = vim.vm.customization.FixedIp()
            adapterMap.adapter.ip.ipAddress = ip
            adapterMap.adapter.subnetMask = subnetMask
            # 在我的环境内，第三个 IP 需要配置网关
            if newip.index(ip) == 2:
                gateway = ".".join(str(ip).split(".")[:3]) + ".1"
                adapterMap.adapter.gateway = gateway
            nicSettingMap.append(adapterMap)

        globalIP = vim.vm.customization.GlobalIPSettings()
        ident = vim.vm.customization.LinuxPrep()
        ident.hostName = vim.vm.customization.FixedName()
        # 主机名设置为 'vm-' + cloudid（只有一位的前面补一个0） + '-' + 5 位随机字符串（不能全部是数字）
        cloudID = str(self.__cloudid)
        if len(cloudID) == 1:
            cloudID = '0' + cloudID

        while True:
            randomStr = ''.join(
                random.choice(string.ascii_lowercase + string.digits) for _ in
                range(5))
            if not randomStr.isdigit():
                break

        randomHostname = "vm-" + cloudID + '-' + randomStr

        ident.hostName.name = randomHostname

        spec = vim.vm.customization.Specification()
        spec.nicSettingMap = nicSettingMap
        spec.globalIPSettings = globalIP
        spec.identity = ident

        try:
            task = vmEntity.CustomizeVM_Task(spec=spec)
            o, m = task_check.task_check(task)
            if o == 'OK':
                msg = ('成功为虚机 {} 配置了 IP。'.format(self.__name))
                log.info(msg)
                code = 0
                return response.return_info(code, msg)
            else:
                msg = ("为虚机 {} 配置 IP 失败：{}".format(self.__name, m.msg))
                log.error(msg)
                code = 1
                return response.return_info(code, msg)

        except vim.fault.CustomizationFault as e:
            msg = e
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

    def vm_relocate(self, host, datastore):
        """
        :param host: 新主机，不可以为空
        :param datastore: 新存储，不可以为空。
        虚机迁移，在我们环境内，由于没有共享存储，用不了 vMotion，迁移只能关机冷迁移。
        要先检查下新存储是否属于新主机，不属于则报错退出。
        """
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if not host:
            msg = "未指定迁移后的主机。"
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if not datastore:
            msg = "未指定迁移后的存储。"
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        hostObj = get_objInfo.get_obj(self.__cloudid, [vim.HostSystem], host)
        if not hostObj:
            msg = "指定的主机 {} 不存在。".format(host)
            log.error(msg)
            code = 1
            return response.return_info(code, msg)
        datastoreObj = get_objInfo.get_obj(self.__cloudid, [vim.Datastore],
                                           datastore)
        if not datastoreObj:
            msg = "指定的存储 {} 不存在。".format(datastore)
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if datastoreObj not in hostObj.datastore:
            msg = "指定的存储 {} 不属于指定的主机 {}。".format(datastore, host)
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        if vmEntity.runtime.powerState == 'poweredon':
            msg = "虚拟机 {} 处于开机状态，请关机后再进行迁移。".format(self.__name)
            log.error(msg)
            code = 1
            return response.return_info(code, msg)

        relocateSpec = vim.vm.RelocateSpec()
        relocateSpec.host = hostObj
        relocateSpec.datastore = datastoreObj

        try:
            task = vmEntity.RelocateVM_Task(relocateSpec)
            o, m = task_check.task_check(task)
            if o == 'OK':
                msg = ("虚机 {} 迁移完毕，当前主机：{}，存储：{}".format(self.__name, host,
                                                         datastore))
                log.info(msg)
                code = 0
                return response.return_info(code, msg)
            else:
                msg = ("虚机 {} 迁移失败：".format(self.__name, m.msg))
                log.error(msg)
                code = 1
                return response.return_info(code, msg)
        except vim.fault.MigrationFault as e:
            msg = ("虚机 {} 迁移失败：".format(self.__name, e))
            log.error(msg)
            code = 1
            return response.return_info(code, msg)


# 递归获取所有快照信息
def vm_snapshot_list(rootsnapshot):
    snapshot_data = []
    for snapshot in rootsnapshot:
        snapInfo = {"Name": snapshot.name,
                    "Description": snapshot.description,
                    "SnapshotObj": snapshot.snapshot}
        snapshot_data.append(snapInfo)
        snapshot_data = snapshot_data + vm_snapshot_list(
            snapshot.childSnapshotList)

    return snapshot_data


if __name__ == "__main__":
    vmEntity = VirtualMachine('api-test', 'ljd-admin', 8)
