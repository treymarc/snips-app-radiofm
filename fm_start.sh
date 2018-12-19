#!/bin/sh
killall rtl_fm
rtl_fm -f $1e6 -s 200000 -r 48000 | aplay -r 48000 -f S16_LE &
#rtl_fm -M wbfm -f $1e6 -s 200000 -r 48000 | aplay -r 48000 -f S16_LE &
