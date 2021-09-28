a = {"allScopes": [{"objectId": "vdnscope-3", "objectTypeName": "VdnScope",
                    "vsmUuid": "423B3B93-BFF4-1234-DC8F-7A310A1CEBC4",
                    "nodeId": "b3fb3674-9abc-4fab-9c6d-ab3922225ef9",
                    "revision": 0, "type": {"name": "VdnScope"},
                    "name": "数据库PAAS", "description": "", "clientHandle": "",
                    "extendedAttributes": [], "isUniversal": "false",
                    "universalRevision": 0, "isTemporal": "false",
                    "id": "vdnscope-3", "clusters": {"clusters": [{"cluster": {
        "objectId": "domain-c7", "objectTypeName": "ClusterComputeResource",
        "vsmUuid": "423B3B93-BFF4-1234-DC8F-7A310A1CEBC4",
        "nodeId": "b3fb3674-9abc-4fab-9c6d-ab3922225ef9", "revision": 33,
        "type": {"name": "ClusterComputeResource"}, "name": "万国数据库群集",
        "scope": {"id": "datacenter-2", "objectTypeName": "Datacenter",
                  "name": "Datacenter"}, "clientHandle": "",
        "extendedAttributes": [], "isUniversal": "false",
        "universalRevision": 0, "isTemporal": "false"}}]},
                    "virtualWireCount": 10, "controlPlaneMode": "UNICAST_MODE",
                    "cdoModeEnabled": "false"}]}

print(a['allScopes'])
