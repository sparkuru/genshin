

## 常规异构编译过程

以某平台某工具源码为例：https://github.com/jingpad-bsp/vendor_sprd_proprietories-source_engpc.git

1.   确定目标架构：`uname -mrs`，*Linux 4.14.98 aarch64*

2.   检查源码中的编译文件 `modules/libadc/Makefile`：

     ```makefile
     ...
     
     INCLUDE_DIRS = -I ../../sprd_fts_inc/
     INCLUDE_DIRS += -I ../../../../kernel/kernel4.14/include/uapi/mtd/
     INCLUDE_DIRS += -I ../../../../kernel/kernel4.4/include/uapi/mtd/
     TARGET = libadc.so
     
     ...
     ```

3.   由 makefile 可知，还需要获取对应平台的 kernel 源码：

     1.   linux 4.14 kernel，https://github.com/strongtz/linux-sprd.git，直接拿出 `include/uapi/mtd` 目录，放到 `includes/` 下
     2.   找到 sprd_fts_inc 目录，放到 `includes/` 下

     最终目录结构：

     ```bash
     .
     ├── includes
     │   ├── mtd
     │   │   ├── inftl-user.h
     │   │   ├── mtd-abi.h
     │   │   ├── mtd-user.h
     │   │   ├── nftl-user.h
     │   │   └── ubi-user.h
     │   └── sprd_fts_inc
     │       ├── android
     │       ├── linux
     │       ├── sprd_fts_cb.h
     │       ├── sprd_fts_diag.h
     │       ├── sprd_fts_list.h
     │       ├── sprd_fts_log.h
     │       ├── sprd_fts_log_inc.h
     │       └── sprd_fts_type.h
     ├── Makefile
     ├── modules
     │   ├── test_module_a
     │   │   ├── Makefile
     │   │   ├── test_module_a_main.c
     │   │   └── test_module_a_main.h
     │   └── test_module_b
     │       ├── Makefile
     │       ├── test_module_b_main.c
     │       └── test_module_b_main.h
     └── readme.md
     
     9 directories, 19 files
     ```

4.   重新编写对应的 Makefile 文件：

     1.   `modules/test_module_a/Makefile`：

          ```makefile
          OBJNAME = test_module_a
          
          CFLAGS = -Wall -g -O -fPIC -DSPRD_FTS_TRACE
          
          INCLUDE_DIRS = -I ../../includes/sprd_fts_inc
          INCLUDE_DIRS += -I ../../includes/mtd/
          TARGET = $(OBJNAME).so
          
          LIBS = -lrt
          
          OBJS = $(OBJNAME).o \
          
          SRCS = $(OBJNAME).c \
          
          all:$(OBJS)
          	$(CC) -shared -fPIC -o $(TARGET) $(OBJS) $(LIBPATH) $(LIBS)
          
          $(OBJS):$(SRCS)
          	$(CC) $(CFLAGS) $(INCLUDE_DIRS) -c $^
          
          install:
          	mkdir -p /tmp/tmp/$(OBJNAME)/
          	cp $(TARGET) /tmp/tmp/$(OBJNAME)/
          
          clean:
          	rm -f *.o
          	rm -f *.so
          ```

     2.   `modules/test_module_b/Makefile`：

          ```makefile
          OBJNAME = test_module_b
          
          CFLAGS = -Wall -g -O -fPIC -DSPRD_FTS_TRACE
          
          INCLUDE_DIRS = -I ../../includes/sprd_fts_inc
          INCLUDE_DIRS += -I ../../includes/mtd/
          TARGET = $(OBJNAME).so
          
          LIBS = -lrt
          
          OBJS = $(OBJNAME).o \
          
          SRCS = $(OBJNAME).c \
          
          all:$(OBJS)
          	$(CC) -shared -fPIC -o $(TARGET) $(OBJS) $(LIBPATH) $(LIBS)
          
          $(OBJS):$(SRCS)
          	$(CC) $(CFLAGS) $(INCLUDE_DIRS) -c $^
          
          install:
          	mkdir -p /tmp/tmp/$(OBJNAME)/
          	cp $(TARGET) /tmp/tmp/$(OBJNAME)/
          
          clean:
          	rm -f *.o
          	rm -f *.so
          ```

     3.   `modules/Makefile`：

          ```makefile
          CC = $(CROSS_COMPILE)gcc
          export CC
          
          SUBDIRS = ./test_module_a ./test_module_b
          
          all:
          	for dir in $(SUBDIRS);\
          	do $(MAKE) -C $$dir ||exit 1;\
          	done
          
          install:
          	for dir in $(SUBDIRS);\
          	do $(MAKE) -C $$dir install||exit 1;\
          	done
          
          clean:
          	for dir in $(SUBDIRS);\
          	do $(MAKE) -C $$dir clean||exit 1;\
          	done
          ```

5.   准备编译环境：

     1.   `sudo apt update && sudo apt install gcc-aarch64-linux-gnu g++-aarch64-linux-gnu binutils-aarch64-linux-gnu`
     2.   指定前缀：`export CROSS_COMPILE=aarch64-linux-gnu-; export ARCH=arm64`，然后使用 `${CROSS_COMPILE}gcc --version` 来检查是否已经成功应用

## docker 编译环境制作

buildenv-docker