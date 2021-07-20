#!/usr/bin/env python3

"""
Written by jdreal.
Github:

To login into vCenter.Return the vCetner service_instance.
"""

from pyVim.connect import SmartConnectNoSSL, Disconnect
import atexit
import argparse
import getpass
import configparser
import sys
from pyVmomi import vmodl


def get_args():
    parser = argparse.ArgumentParser(
        description='Standard Arguments for talking to vCenter'
    )

    parser.add_argument('-s', '--host',
                        required=True,
                        action='store',
                        help='The ip address of the vCenter to connect to')

    parser.add_argument('-o', '--port',
                        type=int,
                        default=443,
                        action='store',
                        help='Port of the vCenter')

    parser.add_argument('-u', '--user',
                        required=True,
                        action='store',
                        help='User name of the vCenter')

    parser.add_argument('-p', '--password',
                        required=True,
                        action='store',
                        help='Password of the vCenter')

    args = parser.parse_args()

    if not args.password:
        args.password = getpass.getpass(
            prompt='Enter the password for vCenter %s and user %s: '
                   % (args.host, args.user)
        )

    return args


def vclogin(cloudid):
    # 注意 sys.path[0] 是最外层 .py 文件的当前路径
    confFile = sys.path[0] + r'/conf/conf.ini'
    config = configparser.ConfigParser()
    config.read(confFile)

    vcConfig = None
    for section in config.sections():
        if int(config[section]['cloudid']) == cloudid:
            vcConfig = config[section]

    if vcConfig is None:
        return -1

    vcHost = vcConfig['vcip']
    vcUser = vcConfig['user']
    vcPass = vcConfig['password']

    try:
        si = SmartConnectNoSSL(
            host=vcHost,
            user=vcUser,
            pwd=vcPass,
            port=443
        )

        atexit.register(Disconnect, si)

        # print("Hello vCenter")

    except vmodl.MethodFault as error:
        print("Login to vCenter failed", error)
        return -1

    return si


if __name__ == "__main__":
    cloudid = 7
    vclogin(cloudid)
