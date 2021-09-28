from src_share import vc_login
from pyVmomi import vim


def vc_instance_check(cloudid):
    si = vc_login.vclogin(cloudid)

    if not isinstance(si, vim.ServiceInstance):
        msg = ("clouid {} 不存在，请检查。".format(cloudid))
        err = {"ERROR": msg}
        return err

    si_content = si.RetrieveContent()

    return si_content


if __name__ == "__main__":
    cloudid = 7
    c = vc_instance_check(cloudid)
    print(c)
