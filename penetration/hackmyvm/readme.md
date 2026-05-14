https://hackmyvm.eu/

## virtualbox and vmware problem

when import `.ova` file from hackmyvm in the first time, shows the error info like this: `AMD-V is being used by another hypervisor (VERR_SVM_IN_USE).` and `VirtualBox can't enable the AMD-V extension. Please disable the KVM kernel extension, recompile your kernel and reboot (VERR_SVM_IN_USE).`

my situation in debian 13, then I have to stop vmware's occupation of kvm ability, do the following things to play the game with virtualbox.

```bash
# 1. stop vmware service
sudo systemctl stop vmware.service vmware-USBArbitrator.service

# 2. temporarily remove kmod
sudo modprobe -r vmnet vmmon kvm_amd kvm
```

network problem. virtualbox doesn't automatically creathe a network interface like vmware does (which interface named vmnet1 and vmnet8), then create it manually.

only `192.168.56.0/21` was accepted in VirtualBox 6.1.28+ on [default](https://docs.oracle.com/en/virtualization/virtualbox/6.0/user/network_hostonly.html), so if you'd like to use a specific subnet like `10.10.3.1/24`, must add it into `/etc/vbox/networks.conf`:

```bash
$ sudo usermod -aG vboxusers $USERNAME

# optional
$ sudo mkdir -p /etc/vbox
$ echo '* 10.10.3.1/24' | sudo tee -a /etc/vbox/networks.conf
* 10.10.3.1/24

# tun off the virtualbox vm first.
$ VBoxManage hostonlyif create
0%...10%...20%...30%...40%...50%...60%...70%...80%...90%...100%
Interface 'vboxnet0' was successfully created

# default to `192.168.56.1`
$ VBoxManage hostonlyif ipconfig vboxnet0 --ip 10.10.3.1 --netmask 255.255.255.0
```

## beginner

| vm         | url                                                    | status |
| ---------- | ------------------------------------------------------ | ------ |
| Gameshell5 | https://hackmyvm.eu/machines/machine.php?vm=Gameshell5 |        |
|            |                                                        |        |
|            |                                                        |        |

