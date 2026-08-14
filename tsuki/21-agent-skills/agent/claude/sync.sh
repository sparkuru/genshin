#!/bin/bash

workdir=$(dirname $(readlink -f $0))

claude_config_path="$HOME/.claude"
src_config_path="$workdir"

ln -sfn "$src_config_path/claude-settings.json" "$claude_config_path/settings.json"
ln -sfn "$src_config_path/claude.md" "$claude_config_path/CLAUDE.md"
