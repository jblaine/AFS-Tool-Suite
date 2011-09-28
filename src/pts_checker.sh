#!/bin/sh
#
#        Author: Jeff Blaine <jblaine@mitre.org> Oct 2000
# Prerequisites: Your passwd file is in NIS
#   Description: Simple script to find PTS users which are in your PTS
#                database but not in you NIS passwd map, and PTS host entries
#                which are in your PTS database but not in your NIS hosts map.
#         Usage: Pipe the output of 'pts listentries -users' to this script

# This needs to be GNU grep that supports -E
GREP=/usr/local/bin/grep

#-----------------------------------------------------------------------------
while read line
do
    PTSID=`echo $line | awk '{print $1}'`
    echo $PTSID > /tmp/ptschecker.tmp
    $GREP -E '(129|128)' /tmp/ptschecker.tmp > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        ypmatch $PTSID hosts.byaddr > /dev/null 2>&1
        if [ $? -eq 1 ]; then
            echo "'$PTSID' is not in hosts.byaddr NIS map."
        fi
    else
        ypmatch $PTSID passwd > /dev/null 2>&1
        if [ $? -eq 1 ]; then
            echo "'$PTSID' is not in passwd NIS map."
        fi
    fi
    sleep 1
done
rm -f /tmp/ptschecker.tmp
