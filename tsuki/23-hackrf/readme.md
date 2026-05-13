first install sdk

```bash
$ lsusb | grep -i hackrf
Bus 001 Device 007: ID 1d50:6089 OpenMoko, Inc. Great Scott Gadgets HackRF One SDR

$ sudo apt install hackrf libhackrf-dev libhackrf0
```

connect to hackrf via usb，type `hackrf_info` for accessment checking

```bash
$ sudo hackrf_info
hackrf_info version: 2024.02.1
libhackrf version: 2024.02.1 (0.9)
Found HackRF
Index: 0
Serial number: 0000000000000000675c62dc310967cf
Board ID Number: 4 (HackRF One)
Firmware Version: v1.7.2 (API:1.07)
Part ID Number: 0xa000cb3c 0x005d4f5e
Hardware Revision: r9
Hardware does not appear to have been manufactured by Great Scott Gadgets.
Hardware supported by installed firmware:
    HackRF One
```

sth software might be useful

1.   gqrx：radio receiver implementation，`sudo apt install gqrx-sdr`
2.   inspectrum：radio signal analyser
3.   hackrf_transfer：raw IQ record / replay
4.   SDR# / SDRangel：cross platform GUI
5.   gps-sdr-sim：gps signal simulator，https://github.com/osqzss/gps-sdr-sim.git

## gps-sdr-sim

研究 GNSS 接收机抗干扰/反欺骗，通过 gps-sdr-sim 将接收到的 gps 信号转换成 IQ 文件，这也是学术标准做法

```bash
$ git clone https://github.com/osqzss/gps-sdr-sim.git

$ cd gps-sdr-sim

$ gcc gpssim.c -lm -O3 --static -o gps-sdr-sim

$ file ./gps-sdr-sim 
./gps-sdr-sim: ELF 64-bit LSB executable, x86-64, version 1 (GNU/Linux), statically linked, BuildID[sha1]=fb4d99c3e7722600b4e51efda549570b815e577e, for GNU/Linux 3.2.0, not stripped

$ ls
bladerf.script  circle_llh.csv  getopt.h            gpssim.bin  IS-GPS-200.pdf  player      rtk            triumphv3.txt
brdc0010.22n    extclk          gps-sdr-sim         gpssim.c    LICENSE         README.md   satellite.csv  ublox.jpg
circle.csv      getopt.c        gps-sdr-sim-uhd.py  gpssim.h    Makefile        rocket.csv  satgen         u-center.png

# brdc0010.22n means 2022-01-01's GPS navigation file, check 'RINEX file' for help
$ ./gps-sdr-sim -e ./brdc0010.22n -l 30.6032020000,121.4665760000,100 -b 8 
Using static location mode.
xyz =  -2868189.1,   4686593.8,   3228158.3
llh =   30.603202,  121.466576,       100.0
Start time = 2022/01/01,00:00:00 (2190:518400)
Duration = 300.0 [sec]
05  110.7  26.3  23177909.2   4.4
10  310.9  15.9  24287275.1   3.6
12  153.9   6.3  25170000.7   8.4
13   50.8  20.6  23569892.3   4.1
15   38.7  48.7  21154261.4   2.4
18  252.5  61.7  20724449.1   2.0
20  123.4   1.6  25460649.0  10.1
23  326.3  46.6  21561248.4   2.2
24  150.9  76.7  20005777.4   2.0
28   58.9   5.4  25423151.8   6.5
29  203.2   0.7  25699722.9   8.5
32  256.7   1.2  25744768.1   4.9
Time into run = 300.0
Done!
Process time = 19.9 [sec]

$ file gpssim.bin
gpssim.bin: data
```

`gps-sdr-sim` convert GPS navigation file into a IQ gpssim.bin file，to be used in hackrf，change its ext to `c8`：`mv gpssim.bin gpssim.c8`