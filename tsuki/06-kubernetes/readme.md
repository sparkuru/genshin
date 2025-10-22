# k8s

k8s cdi cni pvc pv vm vmi pod multus vlan

k3s means k8s-light

## usage

### mirror registry

搭建镜像站：docker registry、harbor 等，采用统一 Docker Registry v2 API 标准

### k8s server

搭建

### kubectl

管理 k8s 服务器中的容器

1.   配置

     1.   获取 `curl -LO https://dl.k8s.io/release/v1.34.0/bin/linux/amd64/kubectl`

     2.   配置文件 `~/.kube/config`

          ```bash
          $ cat ~/.kube/config 
          apiVersion: v1
          clusters:
          - cluster:
              certificate-authority-data: <CERTIFICATE-DATA-OVER-BASE64>
              server: https://ip:api_port
            name: kubernetes
          contexts:
          - context:
              cluster: k8s
              user: k8s-root
            name: k8s-root@k8s
          current-context: k8s-root@kubernetes
          kind: Config
          preferences: {}
          users:
          - name: k8s-root
            user:
              client-certificate-data: <CERTIFICATE-DATA-OVER-BASE64>
              client-key-data: <PRIVATE-KEY-DATA-OVER-BASE64>
          ```

     3.   `kubectl get pods -A` 获取远端 pods 信息

2.   示例单个机器配置文件 `test.yaml`（类似 docker compose 的 yaml）：

     ```yaml
     apiVersion: kubevirt.io/v1
     kind: VirtualMachine
     metadata:
       labels:
         kubevirt.io/vm: <YOUR-VM-LABEL>
       name: <YOUR-VM-NAME>
     spec:
       runStrategy: Halted
       template:
         metadata:
           labels:
             kubevirt.io/vm: <YOUR-VM-LABEL>
         spec:
           domain:
             devices:
               disks:
               - disk:
                   bus: virtio
                 name: containerdisk
             machine:
               type: ""
             resources:
               requests:
                 cpu: 4
                 memory: 8G
           terminationGracePeriodSeconds: 0
           volumes:
           - name: containerdisk
             containerDisk:
               image: <YOUR-OWN-REGISTRY>/devcontainers/python:3.10-bookworm:latest	# 注意这里选择的得是 虚拟机容器磁盘镜像 (带完整 kernel 和 filesystem)，而不是传统的 docker 镜像
     ```

     启用该配置文件

     ```bash
     $ ./kubectl apply -f ./test.yaml
     virtualmachine.kubevirt.io/vm-debian created
     ```

docker 使用的是普通容器镜像，包含应用程序和依赖库，运行在宿主机的内核上，但需要运行在宿主机的 kernel 上，下面是区别：

| 概念           | 英文                | 实际含义                     | 文件格式                       | 存储位置          | 运行方式                     | 使用场景       |
| -------------- | ------------------- | ---------------------------- | ------------------------------ | ----------------- | ---------------------------- | -------------- |
| 容器镜像       | Container Image     | 应用程序 + 依赖 + 文件系统层 | OCI/Docker 镜像格式            | Docker Registry   | Docker/containerd 直接运行   | 运行应用程序   |
| 容器           | Container           | 运行中的容器镜像实例         | 运行时进程 + 文件系统          | 宿主机内存/磁盘   | 共享宿主机内核，进程隔离     | 应用运行时     |
| 虚拟机容器镜像 | ContainerDisk Image | 虚拟机磁盘文件的容器封装     | 外层 OCI 格式 + 内层 qcow2/ISO | Docker Registry   | KubeVirt 提取后给虚拟机使用  | 存储虚拟机磁盘 |
| 虚拟机磁盘     | VM Disk             | 虚拟机的硬盘镜像             | qcow2/raw/vmdk/ISO             | 文件系统/对象存储 | 被虚拟化软件（QEMU/KVM）挂载 | 虚拟机的存储   |
| 虚拟机         | Virtual Machine     | 完整的虚拟化操作系统         | 虚拟硬件 + OS + 应用           | 虚拟化平台        | 独立内核，硬件虚拟化         | 运行完整 OS    |

而 k8s 管理的是虚拟机集群，单位是虚拟机容器磁盘镜像，因此需要将容器景象转换成虚拟机容器磁盘镜像：

```bash
# 导出 容器镜像 (container image) 的文件系统 (rootfs)
$ docker export $(docker create python:3.10-bookworm) -o rootfs.tar

# 转换成 虚拟机磁盘 (vm disk) 格式, 这里是 qcow2
$ virt-make-fs --format=qcow2 --type=ext4 rootfs.tar disk.qcow2

# 打包成 虚拟机容器镜像 (container disk image)
$ cat > Dockerfile <<EOF
FROM scratch
ADD disk.qcow2 /disk/
EOF
$ docker build -t my-vm-image:latest .
```

### virtctl 连通

1.   获取 virtctl：`export VERSION=$(curl https://storage.googleapis.com/kubevirt-prow/release/kubevirt/kubevirt/stable.txt); wget https://github.com/kubevirt/kubevirt/releases/download/${VERSION}/virtctl-${VERSION}-linux-amd64`

2.   `virtctl start <YOUR-VM-NAME>`

3.   virtctl 具体的用法有很多，例如 vnc：`virtctl vnc <YOUR-VM-NAME> --proxy-only`

     ```bash
     $ virtctl vnc <YOUR-VM-NAME> --proxy-only
     {"port":34916}
     ```

## 安装

### k3s

[项目地址](https://github.com/k3s-io/k3s)

```bash
curl -sfL https://get.k3s.io | sh - 
sudo k3s kubectl get node 
```

### kubevirt

[项目地址](https://github.com/kubevirt/kubevirt)

```bash
# Point at latest release
export RELEASE=$(curl https://storage.googleapis.com/kubevirt-prow/release/kubevirt/kubevirt/stable.txt)
# Deploy the KubeVirt operator
kubectl apply -f https://github.com/kubevirt/kubevirt/releases/download/${RELEASE}/kubevirt-operator.yaml
# Create the KubeVirt CR (instance deployment request) which triggers the actual installation
kubectl apply -f https://github.com/kubevirt/kubevirt/releases/download/${RELEASE}/kubevirt-cr.yaml
# wait until all KubeVirt components are up
kubectl -n kubevirt wait kv kubevirt --for condition=Available
```

### Multus CNI

[项目地址](https://github.com/k8snetworkplumbingwg/multus-cni)

```bash
kubectl apply -f https://raw.githubusercontent.com/k8snetworkplumbingwg/multus-cni/master/deployments/multus-daemonset-thick.yml
```

k3s的CNI位置默认与k8s不同，需要手动创建链接或复制

```
sudo ln -sf /var/lib/rancher/k3s/agent/etc/cni/ /etc/cni/
```

### CNI

[项目地址](https://github.com/containernetworking/plugins)

```
CNI_VERSION="v1.3.0"
sudo mkdir -p /opt/cni/bin
curl -L "https://github.com/containernetworking/plugins/releases/download/${CNI_VERSION}/cni-plugins-linux-amd64-${CNI_VERSION}.tgz" | sudo tar -C /opt/cni/bin -xz
```

### CDI

[项目地址](https://github.com/kubevirt/containerized-data-importer)

```
export VERSION=$(basename $(curl -s -w %{redirect_url} https://github.com/kubevirt/containerized-data-importer/releases/latest))
kubectl create -f https://github.com/kubevirt/containerized-data-importer/releases/download/$VERSION/cdi-operator.yaml
kubectl create -f https://github.com/kubevirt/containerized-data-importer/releases/download/$VERSION/cdi-cr.yaml
```