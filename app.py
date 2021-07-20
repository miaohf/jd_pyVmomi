from flask import Flask, jsonify, request
from src_get_info import asset_esxi, vm_area, vm_system, vm_vmsdsmap, asset_vms, \
    asset_vm_resource, asset_datastore, asset_vm_vmsnet, vm_vmsnetwork, \
    asset_vm_datacenter

from src_justdoit import folder_operations, vm_operations

app = Flask(__name__)


@app.route('/', methods=['GET'])
def hello():
    name = 'world'
    if 'name' in request.args:
        name = request.args['name']
    data = {'data': 'hello ' + name}
    return jsonify(data)


@app.route('/api/printarg')
# example: http://127.0.0.1:5000/api/printarg?a=4&b=6
def printarg():
    a = request.args
    return jsonify(a)


@app.route('/api/esxitest')
def esxii():
    esxiInfo = vc_esxi_test.get_esxi_info()
    return jsonify(esxiInfo)


@app.route('/api/<int:cc>/ljd')
def ljd(cc):
    return str(cc)


# 表 PARA_VM_AREA，即 vc 里第一层的虚机文件夹（例如云创新/孵化区）
@app.route('/api/<int:cloudid>/para_vm_area')
def route_vm_area(cloudid):
    vm_areaInfo = flask_vm_area(cloudid)
    return jsonify(vm_areaInfo)


# 表 PARA_VM_SYSTEM，即 vc 里第二层的虚机文件夹（某某项目的文件夹）
@app.route('/api/<int:cloudid>/para_vm_system')
def route_vm_system(cloudid):
    vm_systemInfo = flask_vm_system(cloudid)
    return jsonify(vm_systemInfo)


# 表 PARA_VM_VMSDSMAP，虚拟机和所使用的存储的对应关系
@app.route('/api/<int:cloudid>/para_vm_vmsdsmap')
def route_vm_vmsdsmap(cloudid):
    vm_vmsdsmapInfo = flask_vm_vmsdsmap(cloudid)
    return jsonify(vm_vmsdsmapInfo)


# 表 ASSET_VM_HOSTS，即 ESXI 主机
@app.route('/api/<int:cloudid>/asset_vm_hosts')
def route_esxi(cloudid):
    esxiInfo = flask_esxi(cloudid)
    return jsonify(esxiInfo)


# 表 ASSET_VM_VMS，即虚机表
@app.route('/api/<int:cloudid>/asset_vm_vms')
def route_vms(cloudid):
    vmsInfo = flask_vm_vms(cloudid)
    return jsonify(vmsInfo)


# 表 ASSETT_VM_DATASTORE，存储信息表
@app.route('/api/<int:cloudid>/asset_vm_datastore')
def route_ds(cloudid):
    dsInfo = flask_vm_datastore(cloudid)
    return jsonify(dsInfo)


# 表 ASSETT_VM_RESOURCE，集群、资源池表
@app.route('/api/<int:cloudid>/asset_vm_resource')
def route_resource(cloudid):
    resInfo = flask_vm_resource(cloudid)
    return jsonify(resInfo)


# 表 ASSETT_VM_DATACENTER，数据中心表
@app.route('/api/<int:cloudid>/asset_vm_datacenter')
def route_datacenter(cloudid):
    datacenterInfo = flask_vm_datacenter(cloudid)
    return jsonify(datacenterInfo)


# 表 ASSETT_VM_VMSNET，虚机和其对应的网卡信息表
@app.route('/api/<int:cloudid>/asset_vm_vmsnet')
def route_vmsnet(cloudid):
    vmsnetInfo = flask_vm_vmsnet(cloudid)
    return jsonify(vmsnetInfo)


# 表 PARA_VM_VMSNETWORK，网络标签表
@app.route('/api/<int:cloudid>/para_vm_vmsnetwork')
def route_vmsnetwork(cloudid):
    vmsnetworkInfo = flask_vm_vmsnetwork(cloudid)
    return jsonify(vmsnetworkInfo)


###############################################
#      分      ##      分      ##      分      #
#      隔      ##      隔      ##      隔      #
#      线      ##      线      ##      线      #
###############################################


# 表 PARA_VM_AREA，即 vc 里第一层的虚机文件夹（例如云创新/孵化区）
def flask_vm_area(cloudid):
    vm_areaInfo = vm_area.get_vm_area(cloudid=cloudid)
    return vm_areaInfo


# 表 PARA_VM_SYSTEM，即 vc 里第二层的虚机文件夹（某某项目的文件夹）
def flask_vm_system(cloudid):
    vm_systemInfo = vm_system.get_vm_system(cloudid)
    return vm_systemInfo


# 表 PARA_VM_VMSDSMAP，虚拟机和所使用的存储的对应关系
def flask_vm_vmsdsmap(cloudid):
    vm_vmsdsmapInfo = vm_vmsdsmap.get_vm_vmsdsmap(cloudid)
    return vm_vmsdsmapInfo


# 表 ASSET_VM_HOSTS，即 ESXI 主机
def flask_esxi(cloudid):
    esxiInfo = asset_esxi.get_esxi_info(cloudid)
    return esxiInfo


# 表 ASSET_VM_VMS，即虚机表
def flask_vm_vms(cloudid):
    vm_vmsInfo = asset_vms.get_vm_vms(cloudid)
    return vm_vmsInfo


# 表 ASSETT_VM_DATASTORE，存储信息表
def flask_vm_datastore(cloudid):
    vm_dsInfo = asset_datastore.get_datastore_info(cloudid)
    return vm_dsInfo


# 表 ASSETT_VM_RESOURCE，集群、资源池表
def flask_vm_resource(cloudid):
    vm_resInfo = asset_vm_resource.get_cluster_info(cloudid)
    return vm_resInfo


# 表 ASSETT_VM_DATACENTER，数据中心表
def flask_vm_datacenter(cloudid):
    vm_datacenterInfo = asset_vm_datacenter.get_dc_info(cloudid)
    return vm_datacenterInfo


# 表 ASSETT_VM_VMSNET，虚机和其对应的网卡信息表
def flask_vm_vmsnet(cloudid):
    vm_vmsnetInfo = asset_vm_vmsnet.get_vmnet_info(cloudid)
    return vm_vmsnetInfo


# 表 PARA_VM_VMSNETWORK，网络标签表
def flask_vm_vmsnetwork(cloudid):
    vm_vmsnetworkInfo = vm_vmsnetwork.get_vmnet_info(cloudid)
    return vm_vmsnetworkInfo


###############################################
#      分      ##      分      ##      分      #
#      隔      ##      隔      ##      隔      #
#      线      ##      线      ##      线      #
#   下  面  开  始  都  是  操  作  类  接  口   #
###############################################

# 文件夹操作：新建
"""
newFolder：要新建的文件夹的名字
parentFolder: 新文件夹位于哪个文件夹下
"""


@app.route('/api/<int:cloudid>/folder_create')
def folder_create(cloudid):
    parentFolder = request.args.get('pfolder')
    newFolder = request.args.get('nfolder')

    folder = folder_operations.VmFolder(name=newFolder, pfolder=parentFolder,
                                        cloudid=cloudid)
    return folder.create_folder()


# 删除文件夹
"""
由于文件夹可以存在同名的情况，故需要使用 folder + pfolder 来确认是哪个 folder
"""


@app.route('/api/<int:cloudid>/folder_delete')
def folder_delete(cloudid):
    parentFolder = request.args.get('pfolder')
    folder = request.args.get('folder')

    folder = folder_operations.VmFolder(name=folder, pfolder=parentFolder,
                                        cloudid=cloudid)
    return folder.delete_folder()


# 重命名文件夹
@app.route('/api/<int:cloudid>/folder_rename')
def folder_rename(cloudid):
    parentFolder = request.args.get('pfolder')
    folder = request.args.get('folder')
    newname = request.args.get('newname')

    folder = folder_operations.VmFolder(name=folder, pfolder=parentFolder,
                                        cloudid=cloudid)
    return folder.rename_folder(new_name=newname)


# 检查某文件夹下是否存在某虚机
"""
由于虚拟机可以存在同名的情况，故需要 vmname + pfolder 来一起确定是哪台虚机
"""


@app.route('/api/<int:cloudid>/vm_isexist')
def vm_exist_check(cloudid):
    vmname = request.args.get('vmname')
    parentFolder = request.args.get('pfolder')

    vm = vm_operations.VirtualMachine(name=vmname, pfolder=parentFolder,
                                      cloudid=cloudid)
    return vm.vm_exist_check()


# 删除虚拟机
@app.route('/api/<int:cloudid>/vm_delete')
def vm_delete(cloudid):
    vmname = request.args.get('vmname')
    parentFolder = request.args.get('pfolder')

    vm = vm_operations.VirtualMachine(name=vmname, pfolder=parentFolder,
                                      cloudid=cloudid)
    return vm.vm_delete()


# 重命名虚拟机
@app.route('/api/<int:cloudid>/vm_rename')
def vm_rename(cloudid):
    vmname = request.args.get('vmname')
    parentFolder = request.args.get('pfolder')
    newname = request.args.get('newname')

    vm = vm_operations.VirtualMachine(name=vmname, pfolder=parentFolder,
                                      cloudid=cloudid)
    return vm.vm_rename(newname=newname)


# 打开虚拟机电源
@app.route('/api/<int:cloudid>/vm_poweron')
def vm_poweron(cloudid):
    vmname = request.args.get('vmname')
    parentFolder = request.args.get('pfolder')

    vm = vm_operations.VirtualMachine(name=vmname, pfolder=parentFolder,
                                      cloudid=cloudid)
    return vm.vm_poweron()


# 关闭虚拟机电源
@app.route('/api/<int:cloudid>/vm_poweroff')
def vm_poweroff(cloudid):
    vmname = request.args.get('vmname')
    parentFolder = request.args.get('pfolder')

    vm = vm_operations.VirtualMachine(name=vmname, pfolder=parentFolder,
                                      cloudid=cloudid)
    return vm.vm_poweroff()


# 重启虚拟机
@app.route('/api/<int:cloudid>/vm_reboot')
def vm_reboot(cloudid):
    vmname = request.args.get('vmname')
    parentFolder = request.args.get('pfolder')

    vm = vm_operations.VirtualMachine(name=vmname, pfolder=parentFolder,
                                      cloudid=cloudid)
    return vm.vm_reboot()


# 虚拟机新建快照
@app.route('/api/<int:cloudid>/vm_snapshot_create')
def vm_snapshot_create(cloudid):
    vmname = request.args.get('vmname')
    parentFolder = request.args.get('pfolder')

    vm = vm_operations.VirtualMachine(name=vmname, pfolder=parentFolder,
                                      cloudid=cloudid)
    return vm.vm_snapshot_create()


# 虚拟机删除快照
@app.route('/api/<int:cloudid>/vm_snapshot_delete')
def vm_snapshot_delete(cloudid):
    vmname = request.args.get('vmname')
    parentFolder = request.args.get('pfolder')
    snapToDelete = request.args.get('snaptodelete')

    vm = vm_operations.VirtualMachine(name=vmname, pfolder=parentFolder,
                                      cloudid=cloudid)
    return vm.vm_snapshot_delete(snapshot_name=snapToDelete)


# 虚拟机快照恢复
@app.route('/api/<int:cloudid>/vm_snapshot_revert')
def vm_snapshot_revert(cloudid):
    vmname = request.args.get('vmname')
    parentFolder = request.args.get('pfolder')
    snapToRevert = request.args.get('snaptorevert')

    vm = vm_operations.VirtualMachine(name=vmname, pfolder=parentFolder,
                                      cloudid=cloudid)
    return vm.vm_snapshot_revert(snapshot_name=snapToRevert)


# 虚拟机删除全部快照
@app.route('/api/<int:cloudid>/vm_snapshot_delete_all')
def vm_snapshot_delete_all(cloudid):
    vmname = request.args.get('vmname')
    parentFolder = request.args.get('pfolder')

    vm = vm_operations.VirtualMachine(name=vmname, pfolder=parentFolder,
                                      cloudid=cloudid)
    return vm.vm_snapshot_delete_all()


# 修改虚拟机的内存大小
@app.route('/api/<int:cloudid>/vm_reconfigure_mem')
def vm_reconfig_mem(cloudid):
    vmname = request.args.get('vmname')
    parentFolder = request.args.get('pfolder')
    newmemsize = request.args.get('newmemsize')

    vm = vm_operations.VirtualMachine(name=vmname, pfolder=parentFolder,
                                      cloudid=cloudid)
    return vm.vm_reconfigure_mem(newmemsize=newmemsize)


# 修改虚拟机的CPU数量
@app.route('/api/<int:cloudid>/vm_reconfigure_cpu')
def vm_reconfigure_cpu(cloudid):
    vmname = request.args.get('vmname')
    parentFolder = request.args.get('pfolder')
    newcpunum = request.args.get('newcpunum')

    vm = vm_operations.VirtualMachine(name=vmname, pfolder=parentFolder,
                                      cloudid=cloudid)
    return vm.vm_reconfigure_cpu(newcpunum=newcpunum)


# 为虚拟机添加一块网卡
@app.route('/api/<int:cloudid>/vm_reconfigure_nic_add')
def vm_reconfigure_nic_add(cloudid):
    vmname = request.args.get('vmname')
    parentFolder = request.args.get('pfolder')
    newnicname = request.args.get('newnicname')

    vm = vm_operations.VirtualMachine(name=vmname, pfolder=parentFolder,
                                      cloudid=cloudid)
    return vm.vm_reconfigure_nic_add(newnicname=newnicname)


# 为虚拟机删除一块网卡
@app.route('/api/<int:cloudid>/vm_reconfigure_nic_remove')
def vm_reconfigure_nic_remove(cloudid):
    vmname = request.args.get('vmname')
    parentFolder = request.args.get('pfolder')
    nicnumber = request.args.get('nicnumber')

    vm = vm_operations.VirtualMachine(name=vmname, pfolder=parentFolder,
                                      cloudid=cloudid)
    return vm.vm_reconfigure_nic_remove(nicnumber=nicnumber)


# 为虚拟机新增一块磁盘
@app.route('/api/<int:cloudid>/vm_reconfigure_disk_add')
def vm_reconfigure_disk_add(cloudid):
    vmname = request.args.get('vmname')
    parentFolder = request.args.get('pfolder')
    disksize = request.args.get('disksize')

    vm = vm_operations.VirtualMachine(name=vmname, pfolder=parentFolder,
                                      cloudid=cloudid)
    return vm.vm_reconfigure_disk_add(disksize=disksize)


# 为虚拟机删除一块磁盘
@app.route('/api/<int:cloudid>/vm_reconfigure_disk_remove')
def vm_reconfigure_disk_remove(cloudid):
    vmname = request.args.get('vmname')
    parentFolder = request.args.get('pfolder')
    disknumber = request.args.get('disknumber')

    vm = vm_operations.VirtualMachine(name=vmname, pfolder=parentFolder,
                                      cloudid=cloudid)
    return vm.vm_reconfigure_disk_remove(disknumber=disknumber)


# 从模板克隆虚拟机
@app.route('/api/<int:cloudid>/vm_clone')
def vm_clone(cloudid):
    templatename = request.args.get('templatename')
    templatefolder = request.args.get('templatefolder')
    newvm = request.args.get('newvm')
    newvmpfolder = request.args.get('newvmpfolder')
    newvmhost = request.args.get('newvmhost')
    newvmdatastore = request.args.get('newvmdatastore')

    vm = vm_operations.VirtualMachine(name=templatename, pfolder=templatefolder,
                                      cloudid=cloudid)
    return vm.vm_clone(newvm=newvm,
                       newvmpfolder=newvmpfolder,
                       newvmhost=newvmhost,
                       newvmdatastore=newvmdatastore)


if __name__ == '__main__':
    app.config['JSON_AS_ASCII'] = False
    app.run()
