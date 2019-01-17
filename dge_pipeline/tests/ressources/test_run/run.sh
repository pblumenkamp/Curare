#!/usr/bin/env bash

SCRIPTPATH=`readlink -f $0`

FAILEDRUNS=()
bash "`dirname $SCRIPTPATH`/single_end_run/run.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Single_end"); fi

bash "`dirname $SCRIPTPATH`/paired_end_run/run.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Paired_end"); fi

bash "`dirname $SCRIPTPATH`/zipped_run/run.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Zipped_run"); fi

echo "\n\n"
echo "Aborted runs:"
for run in $FAILEDRUNS; do
	echo $run
done
