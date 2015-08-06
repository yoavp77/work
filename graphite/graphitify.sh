#!/bin/bash

if [ $# -lt 2 ]; then
    echo "usage: `basename $0` <metricname> <metric> <unix timestamp>"
    exit 0
fi

if [ ! -x /usr/bin/nc -a ! -x /bin/nc ]; then
        echo "`basename $0` requires netcat"
        exit 1
fi

TS=$3
if [[ $TS = "" || $TS -lt 0 || $TS -gt $(date +%s) ]]; then
    TS=$(date +%s)
fi

echo "$1 $2 $TS" | nc carbon.example.org 2003
