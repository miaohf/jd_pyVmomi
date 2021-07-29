def id(obj):
    '''
    :param obj: 接收到的 vsphere 对象
    例如对象 vim.Datacenter:datacenter-2，vim.ClusterComputeResource:domain-c439

    然后将该对象这个名字转换成字符串，然后取最后的数字，作为对象的ID
    :return: 需要返回这个字符串的数字，作为该对象的 ID
    '''

    idstr = str(obj).strip("'").split("-")[1]
    id = "".join(list(filter(str.isdigit, idstr)))
    return id
