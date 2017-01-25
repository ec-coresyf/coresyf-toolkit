#!/bin/bash

args=`echo "$*" | sed 's/-\(\S*\)\s\+\([^- ]\S*\)/-\1=\2/g'`
gpt Speckle-Filter $args
