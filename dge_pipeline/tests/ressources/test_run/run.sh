#!/usr/bin/env bash

SCRIPTPATH=`readlink -f $0`

bash "`dirname $SCRIPTPATH`/single_end_run/run.sh"

bash "`dirname $SCRIPTPATH`/paired_end_run/run.sh"
