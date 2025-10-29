
get vmware workstation pro for personal use here (login require): https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Workstation%20Pro&freeDownloads=true

## for linux user

use `sudo vmware-modconfig --console --install-all` to manually install .ko file

use `lsmod | grep vmw` to check the result:

```bash
$ lsmod | grep vmw
vmw_vsock_vmci_transport    49152  0
vsock                  73728  2 vsock_diag,vmw_vsock_vmci_transport
vmw_vmci              110592  1 vmw_vsock_vmci_transport
```

### kernel version over 6.16

if your kernel is 6.16+, try vmware workstation pro version 25h2+

### libxml2.so.2 error

if encounter `/usr/lib/x86_64-linux-gnu/libxml2.so.2` error, try `sudo apt install libxml2` and `sudo ln -sf /usr/lib/x86_64-linux-gnu/libxml2.so.16.0.6 /usr/lib/x86_64-linux-gnu/libxml2.so.2`

use cmd like this to check `libxml2.so.2` issue: 

```bash
$ apt list --installed | grep libxml2
$ ls -la /usr/lib/x86_64-linux-gnu/libxml2.so*
$ ldconfig -p | grep libxml2
```