#!/usr/bin/env python3

"""
Written by jdreal.
Github: 

Get the information about vCetner.
"""

from src_share import vc_login


def get_vc_info(si):
    # si = vc_login_vcenter.vclogin()
    si_content = si.RetrieveContent()
    # vCenter
    vCenter_fullName = si_content.about.fullName
    vCenter_version = si_content.about.version
    vCenter_build = si_content.about.build
    vCenter_instanceUUID = si_content.about.instanceUuid

    # datacenter
    datacenter = si_content.rootFolder.childEntity[0]
    datacenterName = datacenter.name

    # first folder
    firstFolder = datacenter.vmFolder.childEntity[0]
    firstFolderName = firstFolder.name

    # vm's folders
    vmFolders = {}
    for vmFolder in firstFolder.childEntity:
        tempVMArray = []
        for vm in vmFolder.childEntity:
            tempVMArray.append(vm.name)
            vmFolders[vmFolder.name] = tempVMArray

    # datastore's folders
    datastoreFolders = []
    datastoreFolder = datacenter.datastoreFolder.childEntity
    for datastore in datastoreFolder:
        datastoreFolders.append(datastore.name)

    # network's folders
    networkFolders = []
    networkFolder = datacenter.networkFolder.childEntity
    for network in networkFolder:
        networkFolders.append(network.name)

    # output
    vCenter_info = {'version': vCenter_version,
                    'build': vCenter_build,
                    'fullName': vCenter_fullName,
                    'instanceUUID': vCenter_instanceUUID,
                    'datacenterName': datacenterName,
                    'firstFolderName': firstFolderName,
                    'vmFolders': vmFolders,
                    'datastoreFolders': datastoreFolders,
                    'networkFolders': networkFolders}

    return vCenter_info


if __name__ == "__main__":
    cloudid = 7
    si = vc_login.vclogin(cloudid)
    print(get_vc_info(si))
