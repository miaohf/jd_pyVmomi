#!/bin/env python3

import requests
from src_share import get_objInfo, return_info
from pyVmomi import vim


class NsxRest:
    def __init__(self, nsx_manager, cloudid, user, password):
        self.__nsxManager = nsx_manager
        self.__user = user
        self.__password = password
        self.__cloudid = int(cloudid)
        self.header = {"Content-Type": "application/json",
                       "Accept": "application/json"}

    def get_vmid(self, vmpfolder):
        """
        获取某项目虚拟机的 id，并组成一个 list
        :param vmpfolder: 虚拟机的父文件夹，和项目同名
        :return:
        """
        vmPfolder = get_objInfo.get_obj(self.__cloudid, [vim.Folder], vmpfolder)
        if not vmPfolder:
            return -1

        vmIds = []
        for vm in vmPfolder.childEntity:
            vmid = {"objectId": str(vm).strip("'").split(":")[1]}
            vmIds.append(vmid)

        return vmIds

    def add_security_group_with_members(self, vmpfolder):
        """
                创建带有成员的安全组，成员为 folder 下所有虚拟机
                :param vmpfolder: 项目名字
                :return:
                """
        api = "/api/2.0/services/securitygroup/bulk/globalroot-0"
        url = self.__nsxManager + api

        members = self.get_vmid(vmpfolder)
        if members == -1:
            return -1

        securityGroupName = "安全组_" + vmpfolder
        data = {"name": securityGroupName, "members": members}
        response = requests.post(url, headers=self.header,
                                 auth=(self.__user, self.__password),
                                 json=data, verify=False)
        return response

    def add_security_group_with_members_for_flask(self, vmpfolder):
        """
        创建带有成员的安全组，成员为 folder 下所有虚拟机
        :param vmpfolder: 项目名字
        :return:
        """
        response = self.add_security_group_with_members(vmpfolder)
        if isinstance(response, dict):
            return response

        # 201 Created: The request was completed and new resource was
        # created
        if response.status_code == 201:
            msg = response.text
            code = 0
            return return_info.return_info(code, msg)
        else:
            msg = response.text
            code = 1
            return return_info.return_info(code, msg)

    def retrieve_all_srcuritygroups(self):
        """
        查询所有安全组的信息
        :return:
        """
        api = "/api/2.0/services/securitygroup/scope/globalroot-0"
        url = self.__nsxManager + api

        response = requests.get(url, headers=self.header,
                                auth=(self.__user, self.__password),
                                verify=False)

        return response

    def retrieve_all_srcuritygroups_for_flask(self):
        """
        查询所有安全组的信息 for flask
        :return:
        """
        response = self.retrieve_all_srcuritygroups()

        if response.status_code == 200:
            msg = response.json()
            code = 0
            return return_info.return_info(code, msg)
        else:
            msg = response.text
            code = 1
            return return_info.return_info(code, msg)

    def delete_securitygroup(self, sgname):
        """
        删除某个安全组
        :param sgname: 待删除的安全组的名字
        :return:
        """
        # 先查询所有安全组的信息，再根据目标安全组的名字进行过滤
        allSG = self.retrieve_all_srcuritygroups_for_flask()
        if not isinstance(allSG, list):
            raise SystemExit("全部组错误")

        sgID = None
        for sg in allSG:
            if sg['name'] == sgname:
                sgID = sg['objectId']

        if not sgID:
            raise SystemExit("查无此安全组")

        api = "/api/2.0/services/securitygroup/" + sgID
        url = self.__nsxManager + api
        response = requests.delete(url, headers=self.header,
                                   auth=(self.__user, self.__password),
                                   verify=False)

        if response.status_code == 200:
            return response.text
        else:
            return response.text

    def retrieve_dsfirewall_info(self):
        """
        查询分布式防火墙的所有信息，包含 layer2Sections 和 layer3Sections
        :returns: 返回防火墙信息以及查询的 etag
        """
        api = "/api/4.0/firewall/globalroot-0/defaultconfig"
        url = self.__nsxManager + api

        response = requests.get(url, headers=self.header,
                                auth=(self.__user, self.__password),
                                verify=False)

        etag = response.headers["Etag"].strip("\"")

        if response.status_code == 200:
            return response.json(), etag
        else:
            return response.text

    def retrieve_dsfirewall_info_for_flask(self):
        """
        与上一个函数功能一致，只不过是能给 flask 接口正常返回
        查询分布式防火墙的所有信息，包含 layer2Sections 和 layer3Sections
        :returns: 返回防火墙信息以及查询的 etag
        """
        api = "/api/4.0/firewall/globalroot-0/defaultconfig"
        url = self.__nsxManager + api

        response = requests.get(url, headers=self.header,
                                auth=(self.__user, self.__password),
                                verify=False)

        # etag = response.headers["Etag"].strip("\"")

        if response.status_code == 200:
            msg = response.json()
            code = 0
            return return_info.return_info(code, msg)
        else:
            msg = response.text
            code = 1
            return return_info.return_info(code, msg)

    def retrieve_dsfirewall_layer3sections_info_with_etag(self):
        """
        查询分布式防火墙里 layer3Sections 区域的所有信息
        :returns: 返回三层防火墙的信息以及etag
        """
        dsFirewallInfo, etag = self.retrieve_dsfirewall_info()
        if isinstance(dsFirewallInfo, dict):
            layer3Sections = dsFirewallInfo["layer3Sections"]["layer3Sections"]
            return layer3Sections, etag
        else:
            return dsFirewallInfo

    def retrieve_layer3sections_rule_info(self, rule_name):
        """
        在三层防火墙下，根据规则名字查询规则的 id，同时返回 etag 信息
        :rname: 要查询的规则名字
        :return:
        """
        allRules, etag = self.retrieve_dsfirewall_info()
        l3Rules = allRules["layer3Sections"]["layer3Sections"][0]["rules"]
        targetRuleId = None
        for rule in l3Rules:
            if rule["name"] == rule_name:
                targetRuleId = rule["id"]
                break

        return targetRuleId, etag

    def add_rule_for_vmsystem(self, vmpfolder):
        """
        为某个虚拟机项目创建安全组并创建三层防火墙规则
        :param vmpfolder: 虚拟机项目名
        """
        # 先创建安全组，并获取其 ID
        sgResponse = self.add_security_group_with_members(vmpfolder)
        if sgResponse == -1:
            msg = ("项目 {} 不存在。".format(vmpfolder))
            code = 1
            return return_info.return_info(code, msg)

        # 非 0 的话表示安全组创建失败，报错退出
        # 或者表示安全组已经存在，那么对于的防火墙规则也应该已经存在，报错退出
        if sgResponse.status_code != 201:
            code = 1
            return return_info.return_info(code, sgResponse.text)

        sgId = None
        sgName = "安全组_" + vmpfolder
        if sgResponse.status_code == 201:
            sgId = sgResponse.text
        if not sgId:
            msg = ("找不到安全组 {}".format(sgName))
            code = 1
            return return_info.return_info(code, msg)

        # 创建防火墙规则
        layer3Sections, etag = self.retrieve_dsfirewall_layer3sections_info_with_etag()
        sectionId = layer3Sections[0]['id']

        api = "/api/4.0/firewall/globalroot-0/config/layer3sections/" + str(
            sectionId) + "/rules"

        url = self.__nsxManager + api

        header = {"Content-Type": "application/json",
                  "Accept": "application/json",
                  "If-Match": etag}

        data = {"name": vmpfolder,
                "action": "allow",
                "sources": {"excluded": "false", "sourceList": [
                    {"name": sgName, "value": sgId, "type": "SecurityGroup",
                     "isValid": "true"}]},
                "destinations": {"excluded": "false", "destinationList": [
                    {"name": sgName, "value": sgId, "type": "SecurityGroup",
                     "isValid": "true"}]}}

        response = requests.post(url,
                                 headers=header,
                                 auth=(self.__user, self.__password),
                                 json=data,
                                 verify=False)

        if response.status_code == 201:
            msg = response.text
            code = 0
            return return_info.return_info(code, msg)
        else:
            msg = response.text
            code = 1
            return return_info.return_info(code, msg)

    def add_rule_in_layer3sections(self, rname):
        """
        rname 和创建安全组里面的 vmpfolder 是一样的，都是虚拟机的文件夹
        在 三层区域内 新增一条规则，规则名为 rname，与虚拟机的 pfolder 保持一致
        配合之前创建安全组的函数一起使用，源和目的都是 “安全组_rname”
        服务为任意，不用配置。
        """

        # 先获取三层区域的 sectionsid 以及此次 GET 请求的 Etag
        # 将 sectionsid 写入请求 url
        # 将 Etag 写入 header
        layer3Sections, etag = self.retrieve_dsfirewall_layer3sections_info_with_etag()
        sectionId = layer3Sections[0]['id']
        api = "/api/4.0/firewall/globalroot-0/config/layer3sections/" + str(
            sectionId) + "/rules"

        url = self.__nsxManager + api

        header = {"Content-Type": "application/json",
                  "Accept": "application/json",
                  "If-Match": etag}

        # 构造请求体
        sgName = "安全组_" + rname
        # 获取所有安全组信息，然后找到我们需要的安全组的 id
        sgAll = self.retrieve_all_srcuritygroups_for_flask()
        sgId = None
        if isinstance(sgAll, list):
            for sg in sgAll:
                if sg["name"] == sgName:
                    sgId = sg["objectId"]
        if not sgId:
            raise SystemExit("找不到指定的安全组")

        data = {"name": rname,
                "action": "allow",
                "sources": {"excluded": "false", "sourceList": [
                    {"name": sgName, "value": sgId, "type": "SecurityGroup",
                     "isValid": "true"}]},
                "destinations": {"excluded": "false", "destinationList": [
                    {"name": sgName, "value": sgId, "type": "SecurityGroup",
                     "isValid": "true"}]}}

        response = requests.post(url,
                                 headers=header,
                                 auth=(self.__user, self.__password),
                                 json=data,
                                 verify=False)

        if response.status_code == 201:
            return response.text
        else:
            return response.text

    def delete_rule_in_layer3sections(self, rule_name):
        """
        将指定的规则删除
        :param rule_name: 规则名字
        :return:
        """
        ruleId, _ = self.retrieve_layer3sections_rule_info(rule_name)
        if not ruleId:
            print("指定的规则 {} 不存在。")
            return -1

        layer3Sections, etag = self.retrieve_dsfirewall_layer3sections_info_with_etag()
        sectionId = layer3Sections[0]['id']

        api = "/api/4.0/firewall/globalroot-0/config/layer3sections/" + sectionId + "/rules/" + str(
            ruleId)
        url = self.__nsxManager + api

        header = {"Content-Type": "application/json",
                  "Accept": "application/json",
                  "If-Match": etag}

        response = requests.delete(url,
                                   headers=header,
                                   auth=(self.__user, self.__password),
                                   verify=False)

        return response

    def delete_rule_in_layer3sections_for_flask(self, rule_name):
        """
        删除规则 for flask
        """
        response = self.delete_rule_in_layer3sections(rule_name)
        if response.status_code == 204:
            msg = ("规则 {} 删除成功。".format(rule_name))
            code = 0
            return return_info.return_info(code, msg)
        else:
            msg = ("规则 {} 删除失败。".format(rule_name))
            code = 1
            return return_info.return_info(code, msg)


if __name__ == "__main__":
    pass
