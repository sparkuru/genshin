

HOST_URL="vpn.majo.im"
OPENVPN_PORT=1194
CLIENT_NAME="minecraft"

docker run -v $PWD/data:/etc/openvpn --rm kylemanna/openvpn:latest ovpn_genconfig -u udp://$HOST_URL
docker run -v $PWD/data:/etc/openvpn --rm -it kylemanna/openvpn:latest ovpn_initpki
# 输入密码，基本信息
# 生成的配置文件放在容器的 /etc/openvpn/pki 下

docker run -v $PWD/data:/etc/openvpn -d -p $OPENVPN_PORT:1194/udp --cap-add=NET_ADMIN kylemanna/openvpn:latest
# 开放对应端口的 udp 权限

docker run -v $PWD/data:/etc/openvpn --rm -it kylemanna/openvpn:latest easyrsa build-client-full $CLIENT_NAME nopass
docker run -v $PWD/data:/etc/openvpn --rm kylemanna/openvpn:latest ovpn_getclient $CLIENT_NAME > $CLIENT_NAME.ovpn
# $CLIENT_NAME.ovpn 即为客户端连接配置文件
# sudo openvpn --config $CLIENT_NAME.ovpn