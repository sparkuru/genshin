
init

```bash
$ init.sh
Installing frida-tools for the current user
Looking in indexes: https://mirrors.ustc.edu.cn/pypi/simple
Requirement already satisfied: frida-tools in /home/wkyuu/.local/lib/python3.13/site-packages (14.5.0)
Collecting frida-tools
  Downloading https://mirrors.ustc.edu.cn/pypi/packages/80/5e/4592b8005bb5126642c80dfa7ea7a1ab81fd8c232fa03e20374216c04831/frida_tools-14.10.4.tar.gz (4.7 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4.7/4.7 MB 46.2 MB/s eta 0:00:00
  Installing build dependencies ... done
  Getting requirements to build wheel ... done
  Preparing metadata (pyproject.toml) ... done
Requirement already satisfied: colorama<1.0.0,>=0.2.7 in /home/wkyuu/.local/lib/python3.13/site-packages (from frida-tools) (0.4.6)
Collecting frida<18.0.0,>=17.10.0 (from frida-tools)
  Downloading https://mirrors.ustc.edu.cn/pypi/packages/03/80/d3c2d066a9ab25014fd3dae2ca57b1e2cd85369308a9cf9c4b1b3c564a63/frida-17.17.0-cp37-abi3-manylinux_2_5_x86_64.whl (33.3 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 33.3/33.3 MB 40.0 MB/s eta 0:00:00
Requirement already satisfied: prompt-toolkit<4.0.0,>=2.0.0 in /home/wkyuu/.local/lib/python3.13/site-packages (from frida-tools) (3.0.52)
Requirement already satisfied: pygments<3.0.0,>=2.0.2 in /home/wkyuu/.local/lib/python3.13/site-packages (from frida-tools) (2.19.2)
Requirement already satisfied: websockets<14.0.0,>=13.0.0 in /home/wkyuu/.local/lib/python3.13/site-packages (from frida-tools) (13.1)
Requirement already satisfied: wcwidth in /home/wkyuu/.local/lib/python3.13/site-packages (from prompt-toolkit<4.0.0,>=2.0.0->frida-tools) (0.7.0)
Building wheels for collected packages: frida-tools
  Building wheel for frida-tools (pyproject.toml) ... done
  Created wheel for frida-tools: filename=frida_tools-14.10.4-py3-none-any.whl size=4720656 sha256=57507347153c2c052bbbc92d82bc1789a23938c231a03d4d3f4446806c2d16f3
  Stored in directory: /home/wkyuu/.cache/pip/wheels/0b/18/67/5b5ba806bfe677c079262fdb49edb0d71093218c1adb322de0
Successfully built frida-tools
Installing collected packages: frida, frida-tools
  Attempting uninstall: frida
    Found existing installation: frida 17.5.1
    Uninstalling frida-17.5.1:
      Successfully uninstalled frida-17.5.1
  Attempting uninstall: frida-tools
    Found existing installation: frida-tools 14.5.0
    Uninstalling frida-tools-14.5.0:
      Successfully uninstalled frida-tools-14.5.0
Successfully installed frida-17.17.0 frida-tools-14.10.4
Frida 17.17.0 installed at /home/wkyuu/.local/bin/frida
Saving servers to /home/wkyuu/.local/bin/frida-server
Downloading Android arm server
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
100 7049k  100 7049k    0     0  3467k      0  0:00:02  0:00:02 --:--:-- 10.7M
Downloading Android arm64 server
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
100 15.4M  100 15.4M    0     0  7002k      0  0:00:02  0:00:02 --:--:-- 14.6M
Downloading Android x86 server
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
100 15.3M  100 15.3M    0     0  5192k      0  0:00:03  0:00:03 --:--:-- 11.4M
Downloading Android x86_64 server
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
100 30.4M  100 30.4M    0     0  11.6M      0  0:00:02  0:00:02 --:--:-- 26.1M
Frida Android servers are ready

$ tree ~/.local/bin/frida*

frida
frida-apk
frida-compile
frida-create
frida-discover
frida-itrace
frida-join
frida-kill
frida-ls
frida-ls-devices
frida-pm
frida-ps
frida-pull
frida-push
frida-rm
frida-server
├── frida-server-17.17.0-android-arm
├── frida-server-17.17.0-android-arm64
├── frida-server-17.17.0-android-x86
└── frida-server-17.17.0-android-x86_64
frida-strace
frida-trace

1 directory, 21 files
```

then run

```bash
$ connect.sh

== Frida Android connection ==
-- Checking local tools --
-- Inspecting Android device --
-- Checking root access --
Device: F5321 (Android 7.1.1, arm64-v8a)
-- Uploading and starting server --
Uploading frida-server-17.17.0-android-arm64 to /data/local/tmp/frida-server
-- Verifying USB connection --
Frida server is running and USB connection succeeded
Use: /home/wkyuu/.local/bin/frida-ps -U

```