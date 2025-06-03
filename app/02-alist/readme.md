# alist

repo：https://github.com/alist-org/alist.git

1. 创建文件夹 `mkdir -p /home/$USER/docker/02-alist/storage/qbittorrent /home/$USER/docker/02-alist/storage/local /home/$USER/docker/02-alist/data`，

2. 挂载 nas 存储
   1. `sudo apt install cifs-utils`
   
   2. `sudo mount -t cifs //192.168.9.4/nas-torrent /home/$USER/docker/02-alist/nas/nas-torrent -o username=user,password=xxxxx,uid=user,gid=user`
   
   3. `sudo mount -t cifs //192.168.9.4/nas-storage /home/$USER/docker/02-alist/nas/nas-storage -o username=user,password=xxxxx,uid=user,gid=user`
   
   4. 可以将以上操作写到 fstab 中，自动挂载 `sudo vim /etc/fstab`：
   
      ```bash
      # <file system> <mount point> <type> <options> <dump> <pass>
      
      /dev/pve/root / ext4 errors=remount-ro 0 1
      UUID=41F2-21AB /boot/efi vfat defaults 0 1
      /dev/pve/swap none swap sw 0 0
      proc /proc proc defaults 0 0
      /dev/sdb1 /mnt/disk01-5.5t ext4 defaults 0 0
      /dev/sdd1 /mnt/disk02-5.5t ext4 defaults 0 0
      
      # 以下新增
      //192.168.9.4/nas-torrent /home/$USER/docker/02-alist/nas/nas-torrent cifs username=user,password=xxxxx,uid=user,gid=user 0 0
      //192.168.9.4/nas-storage /home/$USER/docker/02-alist/nas/nas-storage cifs username=user,password=xxxxx,uid=user,gid=user 0 0
      ```
   
3. `sudo docker-compose -p 02-alist -f /home/$USER/docker/02-alist/alist.yml up -d` 启动后，在 log 里看默认账密 `admin / xxxxxx`

4. 在访问页面输入账密登陆后，配置 alist
   1. 语言改中文
   1. `个人资料`，修改默认账密
   3. `存储`，添加驱动：
      1. 本机存储，挂载路径 `nas-torrent`，根文件夹路径 `/opt/alist/nas/nas-torrent`
      2. 本机存储，挂载路径 `nas-storage`，根文件夹路径 `/opt/alist/nas/nas-storage`