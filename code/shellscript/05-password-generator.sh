#!/bin/bash

generate_password() {
    local length="$1"
    local seed="$2"

    if [ -z "$length" ]; then
        length=15
        echo "default key length is 15"
    fi

    if [ -z "$seed" ]; then
        echo "Seed is required to generate a deterministic password."
        return 1
    fi

    echo -n "$seed" | openssl dgst -sha256 -binary | openssl base64 | tr -dc 'a-zA-Z0-9-#.' | head -c $length
    echo
}

while [[ $# -gt 0 ]]; do
    key="$1"

    case $key in
        --length)
        length="$2"
        shift # past argument
        shift # past value
        ;;
        --key)
        seed="$2"
        shift # past argument
        shift # past value
        ;;
        *)    # unknown option
        shift # past argument
        ;;
    esac
done

generate_password "$length" "$seed"