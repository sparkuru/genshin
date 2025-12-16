#!/usr/bin/env bash

CONTAINER_NAME="wireguard"
CONFIG_DIR="./config"

show_peer_qr() {
    local peer_name=$1
    if [ -z "$peer_name" ]; then
        echo "Usage: $0 qr <peer_name>"
        echo "Example: $0 qr peer1"
        exit 1
    fi
    docker exec -it $CONTAINER_NAME /app/show-peer $peer_name
}

list_peers() {
    ls -la $CONFIG_DIR/peer_*/
}

show_peer_conf() {
    local peer_name=$1
    if [ -z "$peer_name" ]; then
        echo "Usage: $0 conf <peer_name>"
        exit 1
    fi
    cat $CONFIG_DIR/peer_${peer_name}/peer_${peer_name}.conf
}

restart_container() {
    docker restart $CONTAINER_NAME
}

show_logs() {
    docker logs -f $CONTAINER_NAME
}

case "$1" in
    qr)
        show_peer_qr $2
        ;;
    list)
        list_peers
        ;;
    conf)
        show_peer_conf $2
        ;;
    restart)
        restart_container
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "WireGuard Server Management"
        echo ""
        echo "Usage: $0 {qr|list|conf|restart|logs} [args]"
        echo ""
        echo "Commands:"
        echo "  qr <peer>     Show QR code for peer"
        echo "  list          List all peers"
        echo "  conf <peer>   Show peer config file"
        echo "  restart       Restart container"
        echo "  logs          Show container logs"
        ;;
esac
