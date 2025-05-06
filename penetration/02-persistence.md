# persistence

持久化、backdoor 的编写等



1. 提权
2. 持久化
   1. 基于 mount 实现的隐藏
   2. 

`socat -d -d TCP-LISTEN:8888,reuseaddr,fork SYSTEM:"cat /etc/dropbear/authorized_keys"`

查看 `/etc/inittab`，找 defaultinit

## refer

1. https://hadess.io/the-art-of-linux-persistence/
2. rbash 逃逸大全，https://xz.aliyun.com/t/7642?time__1311=n4%2BxnD0G0%3DG%3DeAK0QbDsA3OxmxOm5i%3DGb4D
3. 