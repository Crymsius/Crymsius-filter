#!/bin/bash
lead=$1
tail=$2
sed -i -e "/$lead/,/$tail/{ /$lead/{p; r insertBases.tmp
        }; /$tail/p; d;}" Crymsius-filter-filterblast.filter

