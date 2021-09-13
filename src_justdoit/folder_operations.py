#!/usr/bin/env python3

"""
Written by jdreal.
Github: 

Some operations for folders in vCenter.
"""

from pyVmomi import vim
from src_share import get_objInfo, vcenter_instance_check, vc_login, logger


class VmFolder:
    def __init__(self, name, pfolder, cloudid):
        self.__name = name
        self.__pfolder = pfolder
        self.__cloudid = cloudid

    def get_folder(self):
        print(self.__name, self.__cloudid)
        # return get_objInfo.get_obj(content, [vim.Folder], self.__name)

    def create_folder(self):
        si = vc_login.vclogin(self.__cloudid)
        datacenter = si.RetrieveContent().rootFolder.childEntity[0]

        log = logger.Logger("vCenter")

        if not self.__pfolder:
            topFolder = datacenter.vmFolder.childEntity[0]
        else:
            topFolder = get_objInfo.get_obj(self.__cloudid, [vim.Folder],
                                            self.__pfolder)
            if not topFolder:
                msg = ("指定的父目录 {} 不存在。".format(self.__pfolder))
                log.error(msg)
                return 'Failed'

        try:
            topFolder.CreateFolder(self.__name)
            msg = ("新目录 '{}' 创建成功。".format(self.__name))
            log.info(msg)
            return 'OK'
        except vim.fault.DuplicateName as e:
            msg = ("新目录 {} 创建失败：{}".format(e.name, e.msg))
            log.error(msg)
            return 'Failed'

    def delete_folder(self):
        """
        pfodler：self 子文件夹的父文件夹
        此函数用来删除给定的文件夹。由于在不同父文件夹（pfolder)下，可能存在名字相同的
        子文件夹。所以需要用户给定父文件夹的名字，以此来确认子文件夹。
        另外，
        """
        global folderToDelete
        log = logger.Logger("vCenter")

        if not self.__pfolder:
            msg = ("未指定 {} 的父文件夹。".format(self.__name))
            log.error(msg)
            return 'Failed'

        pfolderObj = get_objInfo.get_obj(self.__cloudid, [vim.Folder],
                                         self.__pfolder)
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            return 'Failed'

        # 在父文件夹下尝试寻找要删除的子文件夹
        for cfolder in pfolderObj.childEntity:
            if cfolder.name != self.__name:
                continue
            else:
                try:
                    cfolder.Destroy()
                    msg = ("文件夹 '{}' 删除成功。".format(self.__name))
                    log.info(msg)
                    return 'OK'
                except vim.fault.VimFault:
                    msg = ("文件夹 '{}' 删除失败。".format(self.__name))
                    log.error(msg)
                    return 'Failed'

        # 在父文件夹下找不到要删除的子文件夹
        msg = (
            "请重新确认要删除文件夹 {} 的父文件夹是否为 {}。".format(self.__name, self.__pfolder))
        log.error(msg)
        return 'Failed'

        # 确认由前端页面去做
        # do = input("高危操作提醒！！！请确认是否要删除对象 {} ? (yes or no)"
        #            .format(self.__name))
        # if do in ['yes', 'y']:
        #     folderToDelete.Destroy()
        # elif do in ['no', 'n']:
        #     raise SystemExit
        # else:
        #     raise SystemExit("输入错误，请输入(yes/y or no/n)。")

    def rename_folder(self, new_name):
        log = logger.Logger("vCenter")

        if not self.__pfolder:
            msg = ("未指定 {} 的父文件夹。".format(self.__name))
            log.error(msg)
            return 'Failed'

        pfolderObj = get_objInfo.get_obj(self.__cloudid, [vim.Folder],
                                         self.__pfolder)
        if pfolderObj is None:
            msg = ("指定的父文件夹 {} 不存在。".format(self.__pfolder))
            log.error(msg)
            return 'Failed'

        # 在父文件夹下尝试寻找要重命名的子文件夹
        for cfolder in pfolderObj.childEntity:
            if cfolder.name == new_name:
                msg = ("设置的新名字 {} 已被使用，请重新设置。".format(new_name))
                log.error(msg)
                return 'Failed'

            if cfolder.name != self.__name:
                continue
            else:
                try:
                    cfolder.Rename(new_name)
                    msg = ("文件夹 '{}' 已重命名为 {}。".format(self.__name, new_name))
                    log.error(msg)
                    return 'OK'
                except vim.fault.VimFault:
                    msg = ("文件夹 '{}' 重命名失败。".format(self.__name))
                    log.error(msg)
                    return 'Failed'

        msg = (
            "请重新确认要重命名的文件夹 {} 的父文件夹是否为 {}".format(self.__name, self.__pfolder))
        log.error(msg)
        return 'Failed'


if __name__ == "__main__":
    cloudid = 7
