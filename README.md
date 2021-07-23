# jd_pyVmomi

使用 pyvmomi 调用 vSphere 接口的例子

examples for the pyVmomi library

### 项目使用了 pyVmomi + flask 

- pyVmomi 调用 vSphere 的API
- flask 写相关接口

### src_get_info

采集 vCenter 内数据中心、集群、ESXI主机、虚拟机、网络、存储等信息以及互相间的映射关系

### src_justdoit

实现了日常运维工作中，一些常用的操作，例如克隆虚拟机、配置 IP 地址、虚拟机 CPU/内存/磁盘大小的调整以及快照等操作

### src_share

通用模块，例如 vCenter 的登陆，vSphere 对象的获取等。

### conf

vCenter 的登陆信息 