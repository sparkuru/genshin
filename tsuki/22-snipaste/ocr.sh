#!/usr/bin/env bash

set -o pipefail

/usr/bin/tesseract "$@" -l eng+chi_sim |
/usr/bin/perl -Mutf8 -CS -pe '
1 while s/(\p{Han})\h+(\p{Han})/$1$2/g;
s/\h+([，。！？；：、）】》」』])/$1/g;
s/([，。！？；：、（【《「『])\h+/$1/g;
'
