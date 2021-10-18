import sys
import configparser
from src_nsx.nsx_rest import NsxRest


def get_nsx_client():
    confFile = sys.path[0] + r'/conf/conf.ini'
    config = configparser.ConfigParser()
    config.read(confFile)

    nsxManager = config.get("NSX_MANAGER", "nsxmanager")
    nsxUser = config.get("NSX_MANAGER", "user")
    nsxPassword = config.get("NSX_MANAGER", "password")

    nsxRest = NsxRest(nsx_manager=nsxManager,
                      cloudid=8,
                      user=nsxUser,
                      password=nsxPassword)

    return nsxRest


if __name__ == "__main__":
    nsx = get_nsx_client()