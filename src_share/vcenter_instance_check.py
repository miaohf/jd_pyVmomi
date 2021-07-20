from src_share import vc_login
from pyVmomi import vim


def vc_instance_check(cloudid):
    si = vc_login.vclogin(cloudid)
    if not isinstance(si, vim.ServiceInstance):
        msg = "clouid 不存在，请检查。" % cloudid
        error = {"ERROR": msg}
        return error
    si_content = si.RetrieveContent()

    return si_content
