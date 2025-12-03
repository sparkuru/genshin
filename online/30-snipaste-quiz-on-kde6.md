```bash
$ snipaste.appimage --appimage-extract

$ ./snipaste.AppImage --appimage-mount
/tmp/.mount_snipasHvCUoX

$ cd /tmp/.mount_snipasHvCUoX

# 注意 strace 默认输出到 stderr
$ strace -f -t -T -s 4096 -e trace=recvmsg,sendmsg,read,write ./AppRun 2>err-snipaste.log

# 下面的 `10:03:23 recvmsg(6, {msg_name=NULL, msg_namelen=0, msg_iov=[{iov_base="\1\1$\n\0\0\0\0Y\3\0\0\20\0\300\3\373\5\27\4\373\5\27\4\20\4\0\0\0\0\0\0", iov_len=4096}], msg_iovlen=1, msg_controllen=0, msg_flags=0}, 0) = 32 <0.000010>` 应该就是调用截图的关键信息
$ grep "Screenshot " ./snipaste.log -C5
[pid 78548] 10:03:22 write(11, "[2025-12-03 10:03:22.790] [I] Snipper: preparing...\n", 52) = 52 <0.000010>
[pid 78548] 10:03:22 write(11, "[2025-12-03 10:03:22.790] [I] Desktop: QRect(0, 0, 2880 x 1800)\n", 64 <unfinished ...>
[pid 78545] 10:03:22 write(3, "\1\0\0\0\0\0\0\0", 8 <unfinished ...>
[pid 78548] 10:03:22 <... write resumed>) = 64 <0.000013>
[pid 78545] 10:03:22 <... write resumed>) = 8 <0.000012>
[pid 78548] 10:03:22 write(11, "[2025-12-03 10:03:22.790] [I] Screenshot source: org.kde.KWin.ScreenShot2\n", 74) = 74 <0.000010>
[pid 78546] 10:03:22 read(3, "\1\0\0\0\0\0\0\0", 16) = 8 <0.000009>
[pid 78546] 10:03:22 sendmsg(5, {msg_name=NULL, msg_namelen=0, msg_iov=[{iov_base="l\1\0\1,\0\0\0\24\0\0\0\220\0\0\0\1\1o\0\31\0\0\0/org/kde/KWin/ScreenShot2\0\0\0\0\0\0\0\6\1s\0\30\0\0\0org.kde.KWin.ScreenShot2\0\0\0\0\0\0\0\0\2\1s\0\37\0\0\0org.freedesktop.DBus.Properties\0\3\1s\0\3\0\0\0Get\0\0\0\0\0\10\1g\0\2ss\0", iov_len=160}, {iov_base="\30\0\0\0org.kde.KWin.ScreenShot2\0\0\0\0\7\0\0\0Version\0", iov_len=44}], msg_iovlen=2, msg_controllen=0, msg_flags=0}, MSG_NOSIGNAL) = 204 <0.000014>
[pid 78546] 10:03:22 recvmsg(5, {msg_name=NULL, msg_namelen=0, msg_iov=[{iov_base="l\2\1\1\10\0\0\0Y\16\0\0.\0\0\0\6\1s\0\6\0\0\0:1.628\0\0\5\1u\0\24\0\0\0\10\1g\0\1v\0\0\7\1s\0\5\0\0\0:1.20\0\0\0\1u\0\0\4\0\0\0", iov_len=2048}], msg_iovlen=1, msg_controllen=0, msg_flags=MSG_CMSG_CLOEXEC}, MSG_CMSG_CLOEXEC) = 72 <0.000009>
[pid 78546] 10:03:22 recvmsg(5, {msg_namelen=0}, MSG_CMSG_CLOEXEC) = -1 EAGAIN (资源暂时不可用) <0.000007>
[pid 78546] 10:03:22 write(3, "\1\0\0\0\0\0\0\0", 8) = 8 <0.000007>
--
[pid 78547] 10:03:23 <... write resumed>) = 8 <0.000013>
[pid 78545] 10:03:23 recvmsg(6, {msg_name=NULL, msg_namelen=0, msg_iov=[{iov_base="\1\1$\n\0\0\0\0Y\3\0\0\20\0\300\3\373\5\27\4\373\5\27\4\20\4\0\0\0\0\0\0", iov_len=4096}], msg_iovlen=1, msg_controllen=0, msg_flags=0}, 0) = 32 <0.000010>
[pid 78545] 10:03:23 write(4, "\1\0\0\0\0\0\0\0", 8) = 8 <0.000008>
[pid 78545] 10:03:23 write(18, "\1\0\0\0\0\0\0\0", 8) = 8 <0.000011>
[pid 78569] 10:03:23 read(18,  <unfinished ...>
[pid 78548] 10:03:23 write(11, "[2025-12-03 10:03:23.922] [I] Screenshot (0, 0, 2880 x 1743) destination: none\n", 79 <unfinished ...>
[pid 78569] 10:03:23 <... read resumed>"\1\0\0\0\0\0\0\0", 16) = 8 <0.000016>
[pid 78548] 10:03:23 <... write resumed>) = 79 <0.000018>
[pid 78548] 10:03:23 write(11, "[2025-12-03 10:03:23.922] [I] Snipper: about to quit...\n", 56) = 56 <0.000007>
[pid 78547] 10:03:23 recvmsg(6, {msg_name=NULL, msg_namelen=0, msg_iov=[{iov_base="\1\1%\n\0\0\0\0Y\3\0\0\20\0\300\3\373\5\27\4\373\5\27\4\20\4\0\0\0\0\0\0", iov_len=4096}], msg_iovlen=1, msg_controllen=0, msg_flags=0}, 0) = 32 <0.000012>
[pid 78545] 10:03:23 write(4, "\1\0\0\0\0\0\0\0", 8) = 8 <0.000007>

$ grep -i "screenshot" -C5 err-snipaste.log
[pid 92406] 10:14:47 write(3, "\1\0\0\0\0\0\0\0", 8 <unfinished ...>
[pid 92401] 10:14:47 read(4,  <unfinished ...>
[pid 92406] 10:14:47 <... write resumed>) = 8 <0.000015>
[pid 92401] 10:14:47 <... read resumed>"\1\0\0\0\0\0\0\0", 16) = 8 <0.000017>
[pid 92406] 10:14:47 read(3, "\2\0\0\0\0\0\0\0", 16) = 8 <0.000009>
[pid 92401] 10:14:47 write(4, "\1\0\0\0\0\0\0\0", 8 <unfinished ...>
[pid 92408] 10:14:47 write(11, "[2025-12-03 10:14:47.249] [W] DBus call to screenshot failed: The process is not authorized to take a screenshot\n", 113 <unfinished ...>
[pid 92401] 10:14:47 <... write resumed>) = 8 <0.000029>
[pid 92408] 10:14:47 <... write resumed>) = 113 <0.000019>
[pid 92401] 10:14:47 write(4, "\1\0\0\0\0\0\0\0", 8) = 8 <0.000010>
[pid 92408] 10:14:47 write(11, "[2025-12-03 10:14:47.249] [W] Null screenshot\n", 46 <unfinished ...>
[pid 92401] 10:14:47 write(4, "\1\0\0\0\0\0\0\0", 8 <unfinished ...>
[pid 92408] 10:14:47 <... write resumed>) = 46 <0.000017>

$ sudo journalctl -f /usr/bin/kwin_wayland
12月 03 10:40:42 vxworks-host kwin_wayland_wrapper[3126]: kf.windowsystem: static bool KX11Extras::mapViewport() may only be used on X11
12月 03 10:40:46 vxworks-host kwin_wayland_wrapper[3126]: kf.windowsystem: static bool KX11Extras::mapViewport() may only be used on X11
12月 03 10:42:10 vxworks-host kwin_wayland_wrapper[3126]: kf.service.sycoca: The menu spec file ( "" ) contains a Layout or DefaultLayout tag without the mandatory Merge tag inside. Please fix it.
12月 03 10:42:10 vxworks-host kwin_wayland_wrapper[3126]: kf.service.sycoca: The menu spec file ( "" ) contains a Layout or DefaultLayout tag without the mandatory Merge tag inside. Please fix it.
12月 03 10:43:06 vxworks-host kwin_wayland_wrapper[3126]: kf.service.sycoca: The menu spec file ( "" ) contains a Layout or DefaultLayout tag without the mandatory Merge tag inside. Please fix it.
12月 03 10:43:06 vxworks-host kwin_wayland_wrapper[3126]: kf.service.sycoca: The menu spec file ( "" ) contains a Layout or DefaultLayout tag without the mandatory Merge tag inside. Please fix it.
12月 03 10:46:13 vxworks-host kwin_wayland_wrapper[3126]: kf.service.sycoca: The menu spec file ( "" ) contains a Layout or DefaultLayout tag without the mandatory Merge tag inside. Please fix it.
12月 03 10:46:13 vxworks-host kwin_wayland_wrapper[3126]: kf.service.sycoca: The menu spec file ( "" ) contains a Layout or DefaultLayout tag without the mandatory Merge tag inside. Please fix it.
12月 03 10:47:12 vxworks-host kwin_wayland_wrapper[3126]: kf.service.sycoca: The menu spec file ( "" ) contains a Layout or DefaultLayout tag without the mandatory Merge tag inside. Please fix it.
12月 03 10:47:12 vxworks-host kwin_wayland_wrapper[3126]: kf.service.sycoca: The menu spec file ( "" ) contains a Layout or DefaultLayout tag without the mandatory Merge tag inside. Please fix it.
^[^A12月 03 10:48:01 vxworks-host kwin_wayland_wrapper[3126]: kf.windowsystem: static bool KX11Extras::mapViewport() may only be used on X11

$ dbus-monitor "interface='org.kde.KWin.ScreenShot2'"         
signal time=1764730108.407816 sender=org.freedesktop.DBus -> destination=:1.832 serial=2 path=/org/freedesktop/DBus; interface=org.freedesktop.DBus; member=NameAcquired
   string ":1.832"
signal time=1764730108.407834 sender=org.freedesktop.DBus -> destination=:1.832 serial=4 path=/org/freedesktop/DBus; interface=org.freedesktop.DBus; member=NameLost
   string ":1.832"
method call time=1764730110.242367 sender=:1.772 -> destination=org.kde.KWin.ScreenShot2 serial=25 path=/org/kde/KWin/ScreenShot2; interface=org.kde.KWin.ScreenShot2; member=CaptureWorkspace
   array [
      dict entry(
         string "include-cursor"
         variant             boolean false
      )
      dict entry(
         string "native-resolution"
         variant             boolean true
      )
   ]
   file descriptor
         inode: 1212887
         type: fifo
^C

$ cat ~/cargo/bin/snipaste/Snipaste.desktop 
#!/usr/bin/env xdg-open
[Desktop Entry]
Type=Application
Name=Snipaste
Comment=Snip & Paste!
Exec=/home/wkyuu/cargo/bin/snipaste/usr/bin/Snipaste
Icon=/home/wkyuu/cargo/bin/snipaste/Snipaste
Categories=Graphics;ImageProcessing;
X-GNOME-Autostart-Delay=3
X-DBUS-StartupType=Unique
X-DBUS-ServiceName=com.snipaste.Snipaste
X-KDE-autostart-after=panel
X-KDE-StartupNotify=false
X-KDE-UniqueApplet=true
X-KDE-DBUS-Restricted-Interfaces=org.kde.KWin.ScreenShot2
X-AppImage-Version=2.10.8

$ gio launch ~/cargo/bin/snipaste/Snipaste.desktop 
$ gtk-launch Snipaste

$ desktop-file-install --dir=$HOME/.local/share/applications ./Snipaste.desktop
# 或
$ ln -s ~/cargo/bin/snipaste/Snipaste.desktop ~/.local/share/applications/snipaste.desktop

$ kbuildsycoca5; kbuildsycoca6
kbuildsycoca5 running...
kf.service.sycoca: The menu spec file ( "" ) contains a Layout or DefaultLayout tag without the mandatory Merge tag inside. Please fix it.
kf.service.sycoca: The menu spec file ( "" ) contains a Layout or DefaultLayout tag without the mandatory Merge tag inside. Please fix it.
kbuildsycoca6 running...
kf.service.sycoca: The menu spec file ( "" ) contains a Layout or DefaultLayout tag without the mandatory Merge tag inside. Please fix it.
kf.service.sycoca: The menu spec file ( "" ) contains a Layout or DefaultLayout tag without the mandatory Merge tag inside. Please fix it.
```

解决方式，在 kde 里添加快捷快捷键绑定：`/home/wkyuu/cargo/bin/snipaste/AppRun snip;kbuildsycoca5;kbuildsycoca6`

原因：dbus 的授权机制，让非注册的 desktop 拒绝截屏（不知道为什么 snipaste 会把注册的内容去掉）

因此要不让 dbus 能找到对应的句柄去授权，要不就一直循环检查和注册 desktop（通过上面的快捷键钩子实现）