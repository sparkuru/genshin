#!/bin/bash

WORKDIR=$(
	cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd
)

BURPSUITE_HOME="$HOME/cargo/bin/burpsuite"
BP_HOST_FILE="$BURPSUITE_HOME/bp.host"

ln -sf $WORKDIR/bp.host $BP_HOST_FILE
cp -f $WORKDIR/BurpSuiteCommunity $BURPSUITE_HOME/BurpSuiteCommunity
