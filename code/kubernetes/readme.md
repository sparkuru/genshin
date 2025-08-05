
k8s cdi cni pvc pv vm vmi pod multus vlan

k3s means k8s-light

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