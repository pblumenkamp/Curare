#!/usr/bin/env bash

SCRIPTPATH=$(readlink -f "$0")

FAILEDRUNS=()

for x in */run_with_conda.sh; do
    testName=`dirname ${x}`
    echo "Test: ${x}"
    bash "`dirname $SCRIPTPATH`/${x}"
    if [ $? -ne 0 ]; then FAILEDRUNS+=(${testName}); fi
done

echo -e "\n\n"
echo "Aborted runs:"
for run in "${FAILEDRUNS[@]}"; do
	echo "$run"
done
