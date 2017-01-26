#!/bin/bash 
args=`sed 's/-\(\S\+\)\(\(\s\+[^- ]\S\+\)\+\)/-\1="\2"/g' <<< $@`
args=`sed 's/"\s*\(\S\+\)\s*"/"\1"/g' <<< $args`
echo "$args"
gpt Speckle-Filter $args
