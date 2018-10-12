#!/bin/bash
datetime=$1
file=$2
sed -i -e "s,[0-9]\{4\}.[0-9]\{2\}.[0-9]\{2\}_[0-9]\{2\}:[0-9]\{2\},$datetime," $file