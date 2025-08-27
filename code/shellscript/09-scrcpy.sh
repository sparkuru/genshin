#!/bin/bash

width=486
height=1056

opts=(
  "keyboard=uhid"
  "turn-screen-off"
  "stay-awake"
  "no-audio"
  "no-audio-playback"
  "window-width=$width"
  "window-height=$height"
)

base_cmd=scrcpy
args=""
for opt in ${opts[@]}; do
  args="$args --$opt "
done

cmd="$base_cmd $args"
/bin/bash -c "$cmd"