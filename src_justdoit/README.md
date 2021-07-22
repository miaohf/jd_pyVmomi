# src_get_info



# src_justdoit

定义了虚拟机类`VirtualMachine`，具有若干方法

## vm_configure_ipaddress（）

该方法用来给虚拟机配置 IP 地址，该操作需要用到 [CustomizeVM_Task](https://vdc-download.vmware.com/vmwb-repository/dcr-public/790263bc-bd30-48f1-af12-ed36055d718b/e5f17bfc-ecba-40bf-a04f-376bbb11e811/vim.VirtualMachine.html#customize) 函数，通过指定虚机配置文件 [CustomizationSpec](https://vdc-download.vmware.com/vmwb-repository/dcr-public/790263bc-bd30-48f1-af12-ed36055d718b/e5f17bfc-ecba-40bf-a04f-376bbb11e811/vim.vm.customization.Specification.html) 中的 **nicSettingMap** 来给虚拟机配置 IP。**nicSettingMap** 用来给指定的网卡配置指定的 IP，正是我们需要的。

:bulb:要注意的是，CustomizeVM_TASK 要求虚机处于关机状态。

