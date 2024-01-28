#!/bin/sh

function color() {
    echo -e "\e[33m$1\e[0m"
}

workdir="/opt/acme"
home_acme_dir="/home/$USER/.acme.sh"
DOMAIN='domain.top'
SUB_DOMAIN_LIST=(   # 泛域名
    '\*'
)
KEY_FILE_PATH="$workdir/cert/$DOMAIN.key"
CERT_FILE_PATH="$workdir/cert/$DOMAIN.cer"
FULLCHAIN_FILE_PATH="$workdir/cert/fullchain.cer"

if [ ! -d "$home_acme_dir" ]; then
    cmd="curl https://get.acme.sh | sh -s email=my@example.com"
    color "no $home_acme_dir found, run $cmd first."
    exit
fi

if [ ! -d $workdir ]; then
    mkdir -p $workdir
fi

cd $workdir
. "$home_acme_dir/acme.sh.env"

export Ali_Key="xxxxx"   # 参考这篇文章：https://blog.csdn.net/chen249191508/article/details/98088553
export Ali_Secret="xxxxx"  # AccessKey ID 就是 Ali_Key，AccessKey Secret 就是 Ali_Secret

if [[ $1 == 'issue' ]]; then
    base_cmd="acme.sh --issue --dns dns_ali -d $DOMAIN --force"
    for sub in "$SUB_DOMAIN_LIST[@]"; do
        base_cmd+=" -d $sub.$DOMAIN"
    done
fi

# $DOMAIN.cer 是证书文件, $DOMAIN.key 是密钥文件, fullchain.cer 是全链接文件
if [[ $1 == 'install' ]]; then
    reloadcmd="sudo systemctl restart nginx"
    base_cmd="acme.sh --install-cert --key-file $KEY_FILE_PATH --cert-file $CERT_FILE_PATH --fullchain-file $FULLCHAIN_FILE_PATH --reloadcmd '$reloadcmd' -d $DOMAIN"
    for sub in "${SUB_DOMAIN_LIST[@]}"; do
        base_cmd+=" -d $sub.$DOMAIN"
    done
fi

if [[ $1 == 'info' ]]; then
    base_cmd="acme.sh --info -d $DOMAIN"
    for sub in "${SUB_DOMAIN_LIST[@]}"; do
        base_cmd+=" -d $sub.$DOMAIN"
    done
fi

color "执行: $base_cmd"
if [[ $2 == 'run' ]]; then
    if [[ $3 == 'debug' ]]; then
        base_cmd+=" --debug"
    fi
    eval $base_cmd
fi