#!/usr/bin/env python3

"""
Written by jdreal.
Github: 

Some
"""

from pyVmomi import vim
from src_share import get_objInfo, logger, get_obj_id, task_check, vc_login
import argparse
import time


def get_args():
    """
    参数 -h 是可选的，因为后面代码里会设置新虚机所在主机与模板主机保持一致，这样克隆的速度比较快。
    :return:
    """
    parse = argparse.ArgumentParser(
        description='Arguments for clone a VM from template'
    )

    parse.add_argument('-v', '--vmName',
                       action='store',
                       required=True,
                       help='Name of the VM')

    parse.add_argument('-o', '--operate',
                       required=True,
                       action='store',
                       help='Operation to do')

    parse.add_argument('-f', '--folderName',
                       action='store',
                       help='Folder of the VM')

    parse.add_argument('-t', '--templateName',
                       action='store',
                       help='Name of the template')

    parse.add_argument('-s', '--hostName',
                       action='store',
                       help='Host ip of the host.Use -s to avoid '
                            'conflicting with -h')

    parse.add_argument('-d', '--datastoreName',
                       action='store',
                       help='Name of the datastore')

    parse.add_argument('-n', '--newName',
                       action='store',
                       help='New name of VM(Used when operate=rename')

    parse.add_argument('-x', '--snapshotName',
                       action='store',
                       help="The name of a vm snapshot")

    parse.add_argument('-m', '--memorySize',
                       action='store',
                       type=int,
                       help="New memory size in MB")

    parse.add_argument('-c', '--cpuNum',
                       action='store',
                       type=int,
                       help="Number of virtual processors")

    parse.add_argument('-i', '--networkName',
                       action='store',
                       help='Name of a nic')

    my_args = parse.parse_args()
    return my_args


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
            return 'Failed'

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
                    return 'OK'

        msg = (
            "文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder, self.__name))
        log.error(msg)
        return 'Failed'

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

    def vm_clone(self, newvm, newvmpfolder, newvmhost, newvmdatastore):
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
                return 'Failed'

            if templateToClone is None:
                msg = ("指定的模板 {} 不存在。".format(self.__name))
                log.error(msg)
                return 'Failed'

        if not newvm:
            msg = "为指定新虚机名字。"
            log.error(msg)
            return 'Failed'

        # 检查新虚机的目录是否存在
        folderToClone = get_objInfo.get_obj(self.__cloudid, [vim.Folder],
                                            newvmpfolder)
        if not folderToClone:
            msg = ("指定的新虚机的父文件夹 {} 不存在。".format(newvmpfolder))
            log.error(msg)
            return 'Failed'

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
            return 'Failed'

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
            return 'Failed'

        if datastoreToClone not in hostToClone.datastore:
            msg = (
                "指定的存储 {} 不属于主机 {}。".format(datastoreToClone.name,
                                            hostToClone.name))
            log.error(msg)
            return 'Failed'

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
            task_check.task_check(task)
            msg = ("新虚机 {} 克隆成功。".format(newvm))
            log.info(msg)
            return 'OK'
        except vim.fault.RuntimeFault as e:
            msg = ("新虚机 {} 克隆失败。".format(newvm))
            log.info(msg)
            return 'Failed'

    def vm_delete(self):
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            return 'Failed'

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            return 'Failed'

        if vmEntity.runtime.powerState == "poweredOn":
            msg = ("虚拟机 {} 当前处于开机状态，无法删除。".format(self.__name))
            log.error(msg)
            return 'Failed'

        try:
            task = vmEntity.Destroy_Task()
            task_check.task_check(task)
            msg = ("虚机 {} 已被成功删除。".format(self.__name))
            log.info(msg)
            return 'OK'
        except vim.fault.VimFault as e:
            msg = ("虚机 {} 删除失败。".format(self.__name)) + e
            log.error(msg)
            return 'Failed'

    def vm_rename(self, newname):
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            return 'Failed'

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            return 'Failed'

        try:
            vmEntity.Rename(newname)
            msg = ("虚机 {} 成功重命名为 {}。".format(self.__name, newname))
            log.info(msg)
            return 'OK'
        except vim.fault.VimFault as e:
            msg = ("虚机 {} 重命名失败。".format(self.__name)) + e
            log.error(msg)
            return 'Failed'

    def vm_poweroff(self):
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            return 'Failed'

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            return 'Failed'

        if vmEntity.runtime.powerState == "poweredOff":
            msg = ("虚拟机 {} 当前已经处于关机状态，无法关闭电源。".format(self.__name))
            log.error(msg)
            return 'Failed'

        try:
            task = vmEntity.PowerOff()
            task_check.task_check(task)
            msg = ("虚机 {} 已成功关闭电源。".format(self.__name))
            log.info(msg)
            return 'OK'
        except vim.fault.VimFault as e:
            msg = ("虚机 {} 关闭电源失败。".format(self.__name)) + e
            log.error(msg)
            return 'Failed'

    def vm_poweron(self):
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            return 'Failed'

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            return 'Failed'

        if vmEntity.runtime.powerState == "poweredOn":
            msg = ("虚拟机 {} 当前已经处于开机状态，无法打开电源。".format(self.__name))
            log.error(msg)
            return 'Failed'

        try:
            task = vmEntity.PowerOn()
            task_check.task_check(task)
            msg = ("虚机 {} 已成功打开电源。".format(self.__name))
            log.info(msg)
            return 'OK'
        except vim.fault.VimFault as e:
            msg = ("虚机 {} 打开电源失败。".format(self.__name)) + e
            log.error(msg)
            return 'Failed'

    def vm_reboot(self):
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            return 'Failed'

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            return 'Failed'

        try:
            vmEntity.RebootGuest()
            msg = ("虚机 {} 已成功重启。".format(self.__name))
            log.info(msg)
            return 'OK'
        except vim.fault.InvalidPowerState as e:
            msg = ("虚机 {} 重启失败。".format(self.__name)) + e.msg
            log.error(msg)
            return 'Failed'

    def vm_snapshot_create(self):
        """
        为虚机打快照，快照名字和描述根据当时的时间来定义。
        """
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            return 'Failed'

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            return 'Failed'

        localTime = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime())

        snapshotName = self.__name + "_" + localTime
        snapshotDescription = "snapshot for vm '" + self.__name + "' " + \
                              localTime

        try:
            task = vmEntity.CreateSnapshot(name=snapshotName,
                                           description=snapshotDescription,
                                           memory=False,
                                           quiesce=False)
            task_check.task_check(task)
            msg = ("成功为虚机 {} 新建快照 {}。".format(self.__name, snapshotName))
            log.info(msg)
            return 'OK'
        except vim.fault.SnapshotFault as e:
            msg = ("虚机 {} 快照新建失败。".format(self.__name)) + e.msg
            log.error(msg)
            return 'Failed'

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
            return 'Failed'

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            return 'Failed'

        if vmEntity.snapshot is None:
            msg = ("虚机 {} 不存在任何快照。".format(self.__name))
            log.error(msg)
            return 'Failed'

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
            return 'Failed'

        try:
            task = snapshotDel.RemoveSnapshot_Task(removeChildren=False)
            task_check.task_check(task)
            msg = ("成功删除虚机 {} 的快照 {}。".format(self.__name, snapshot_name))
            log.info(msg)
            return 'OK'
        except vim.fault.SnapshotFault as e:
            msg = ("虚机 {} 的快照 {} 删除失败。".format(self.__name,
                                               snapshot_name)) + e.msg
            log.error(msg)
            return 'Failed'

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
            return 'Failed'

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            return 'Failed'

        if vmEntity.snapshot is None:
            msg = ("虚机 {} 不存在任何快照。".format(self.__name))
            log.error(msg)
            return 'Failed'

        rootSnapshot = vmEntity.snapshot.rootSnapshotList
        snapshotList = vm_snapshot_list(rootSnapshot)

        snapshotRevert = None
        for snapshot in snapshotList:
            if snapshot_name == snapshot["Name"]:
                snapshotRevert = snapshot["SnapshotObj"]

        if snapshotRevert is None:
            msg = ("虚机 {} 下找不到快照 {}。".format(self.__name, snapshot_name))
            log.error(msg)
            return 'Failed'

        try:
            task = snapshotRevert.RevertToSnapshot_Task()
            task_check.task_check(task)
            msg = ("成功将虚机 {} 恢复到快照 {}。".format(self.__name, snapshot_name))
            log.info(msg)
            return 'OK'
        except vim.fault.SnapshotFault as e:
            msg = ("虚机 {} 恢复到快照 {} 失败。".format(self.__name,
                                               snapshot_name)) + e.msg
            log.error(msg)
            return 'Failed'

    def vm_snapshot_delete_all(self):
        """
        delete all the snapshots of a VM
        """
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            return 'Failed'

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            return 'Failed'

        if vmEntity.snapshot is None:
            msg = ("虚机 {} 不存在任何快照。".format(self.__name))
            log.error(msg)
            return 'Failed'

        try:
            task = vmEntity.RemoveAllSnapshots_Task()
            task_check.task_check(task)
            msg = ("成功将虚机 {} 的所有快照删除。".format(self.__name))
            log.info(msg)
            return 'OK'
        except vim.fault.SnapshotFault as e:
            msg = ("虚机 {} 的所有快照删除失败。".format(self.__name)) + e.msg
            log.error(msg)
            return 'Failed'

    def vm_reconfigure_mem(self, newmemsize):
        newmemsize = int(newmemsize)
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            return 'Failed'

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            return 'Failed'

        if not newmemsize:
            msg = ("未指定新的内存大小(G)，无法重新配置虚机 {}。".format(self.__name))
            log.error(msg)
            return 'Failed'

        currentMem = vmEntity.summary.config.memorySizeMB
        if currentMem / 1024 == newmemsize:
            msg = ("虚机 {} 当前内存大小等于新指定的内存大小。".format(self.__name))
            log.error(msg)
            return 'Failed'

        if vmEntity.summary.runtime.powerState == "poweredOn":
            msg = ("虚机 {} 当前处于开机状态，无法重新配置内存大小。".format(self.__name))
            log.error(msg)
            return 'Failed'

        spec = vim.vm.ConfigSpec()
        spec.memoryMB = newmemsize * 1024

        try:
            task = vmEntity.ReconfigVM_Task(spec=spec)
            task_check.task_check(task)
            msg = ("成功将虚机 {} 的内存调整为 {} GB。".format(self.__name, newmemsize))
            log.info(msg)
            return 'OK'
        except vim.fault.VmConfigFault as e:
            msg = ("调整虚机 {} 内存失败。".format(self.__name)) + e.msg
            log.error(msg)
            return 'Failed'

    def vm_reconfigure_cpu(self, newcpunum):
        newcpunum = int(newcpunum)
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            return 'Failed'

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            return 'Failed'

        if not newcpunum:
            msg = ("未指定新的CPU数量，无法重新配置虚机 {}。".format(self.__name))
            log.error(msg)
            return 'Failed'

        currentCpuNum = vmEntity.summary.config.numCpu
        if currentCpuNum == newcpunum:
            msg = ("虚机 {} 当前内存大小等于新指定的CPU数量。".format(self.__name))
            log.error(msg)
            return 'Failed'

        if vmEntity.summary.runtime.powerState == "poweredOn":
            msg = ("虚机 {} 当前处于开机状态，无法重新配置CPU数量。".format(self.__name))
            log.error(msg)
            return 'Failed'

        spec = vim.vm.ConfigSpec()
        spec.numCPUs = newcpunum

        try:
            task = vmEntity.ReconfigVM_Task(spec=spec)
            task_check.task_check(task)
            msg = ("成功将虚机 {} 的CPU数量调整为 {} 。".format(self.__name, newcpunum))
            log.info(msg)
            return 'OK'
        except vim.fault.VmConfigFault as e:
            msg = ("调整虚机 {} CPU数量失败。".format(self.__name)) + e.msg
            log.error(msg)
            return 'Failed'

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
            return 'Failed'

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            return 'Failed'

        if not newnicname:
            msg = "未指定要添加的网卡名。"
            log.error(msg)
            return 'Failed'

        newNicObj = get_objInfo.get_obj(self.__cloudid, [vim.Network],
                                        newnicname)
        if newNicObj is None:
            msg = ("指定的网卡 {} 不存在。".format(newnicname))
            log.error(msg)
            return 'Failed'

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
            task_check.task_check(task)
            msg = ("成功为虚机 {} 添加了一块网卡 {} 。".format(self.__name, newnicname))
            log.info(msg)
            return 'OK'
        except vim.fault.VmConfigFault as e:
            msg = ("虚机 {} 添加网卡 {} 失败。".format(self.__name, newnicname)) + e.msg
            log.error(msg)
            return 'Failed'

    def vm_reconfigure_nic_remove(self, nicnumber, ):
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            return 'Failed'

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            return 'Failed'

        if not nicnumber:
            msg = "未指定要删除的网卡序号。"
            log.error(msg)
            return 'Failed'

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
            return 'Failed'

        # 配置 vim.vm.device.VirtualDeviceSpec()，将 operation 设置为 remove
        nicSpec = vim.vm.device.VirtualDeviceSpec()
        nicSpec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
        nicSpec.device = nicDeviceToRemove

        spec = vim.vm.ConfigSpec()
        spec.deviceChange = [nicSpec]

        try:
            task = vmEntity.ReconfigVM_Task(spec=spec)
            task_check.task_check(task)
            msg = ("成功为虚机 {} 第 {} 块网卡。".format(self.__name, nicnumber))
            log.info(msg)
            return 'OK'
        except vim.fault.VmConfigFault as e:
            msg = ("虚机 {} 删除第 {} 块网卡失败。".format(self.__name, nicnumber)) + e.msg
            log.error(msg)
            return 'Failed'

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
            return 'Failed'

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            return 'Failed'

        if not disksize:
            msg = "未指定新增磁盘大小。"
            log.error(msg)
            return 'Failed'

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
            task_check.task_check(task)
            msg = ("成功为虚机 {} 新增了一块 {}GB 的磁盘。".format(self.__name, disksize))
            log.info(msg)
            return 'OK'
        except vim.fault.VmConfigFault as e:
            msg = ("虚机 {} 新增磁盘失败。".format(self.__name)) + e.msg
            log.error(msg)
            return 'Failed'

    def vm_reconfigure_disk_remove(self, disknumber):
        log = logger.Logger("vCenter_vm_operations")
        vmEntity, pfolderObj = self.get_vm_obj()
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            return 'Failed'

        if vmEntity is None:
            msg = ("文件夹 {} 下不存在任何虚机或者找不到虚拟机 {}。".format(self.__pfolder,
                                                        self.__name))
            log.error(msg)
            return 'Failed'

        if not disknumber:
            msg = "未指定新增磁盘序号。"
            log.error(msg)
            return 'Failed'

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
            return 'Failed'

        diskLabel = diskPrefixLabel + str(disknumber)
        diskDevice = None
        for dev in vmEntity.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualDisk) and \
                    dev.deviceInfo.label == diskLabel:
                diskDevice = dev
        if not diskDevice:
            msg = "虚机 {} 下找不到磁盘序号为 {} 的磁盘。".format(self.__name, disknumber)
            log.error(msg)
            return 'Failed'

        diskSpec = vim.vm.device.VirtualDeviceSpec()
        diskSpec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
        diskSpec.device = diskDevice

        spec = vim.vm.ConfigSpec()
        spec.deviceChange = [diskSpec]

        try:
            task = vmEntity.ReconfigVM_Task(spec=spec)
            task_check.task_check(task)
            msg = ("成功为虚机 {} 删除了第 {} 块磁盘。".format(self.__name, disknumber))
            log.info(msg)
            return 'OK'
        except vim.fault.VmConfigFault as e:
            msg = ("虚机 {} 删除第 {} 块磁盘失败。".format(self.__name,
                                                disknumber)) + e.msg
            log.error(msg)
            return 'Failed'


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
    si = vc_login.vclogin()
    content = si.RetrieveContent()
    args = get_args()
    vm = VirtualMachine(args.vmName)

    if args.operate == "get":
        vm.get_vm()
    elif args.operate == "clone":
        vm.vm_clone()
    elif args.operate == "rename":
        vm.vm_rename()
    elif args.operate == "poweroff":
        vm.vm_poweroff()
    elif args.operate == "poweron":
        vm.vm_power_on()
    elif args.operate == "reboot":
        vm.vm_reboot()
    elif args.operate == "createsnapshot":
        vm.vm_snapshot_create()
    elif args.operate == "deletesnapshot":
        vm.vm_snapshot_delete(args.snapshotName)
    elif args.operate == "deleteallsnapshot":
        vm.vm_snapshot_delete_all()
    elif args.operate == "listsnapshot":
        vm = get_objInfo.get_obj(content, [vim.VirtualMachine], args.vmName)
        print(vm_snapshot_list(vm.snapshot.rootSnapshotList))
    elif args.operate == "revertsnapshot":
        vm.vm_snapshot_revert(args.snapshotName)
    elif args.operate == "reconfigmem":
        vm.vm_reconfigure_mem()
    elif args.operate == "reconfigcpu":
        vm.vm_reconfig_cpu()
    elif args.operate == "addnic":
        vm.vm_reconfigure_nic_add()
    else:
        raise ValueError('[ERROR] Wrong parameters.Use -h to see parameters.')