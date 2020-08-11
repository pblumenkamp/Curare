#!/usr/bin/env bash

SCRIPTPATH=$(readlink -f "$0")

FAILEDRUNS=()
bash "`dirname $SCRIPTPATH`/single_end_run/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Single_end"); fi

bash "`dirname $SCRIPTPATH`/paired_end_run/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Paired_end"); fi

bash "`dirname $SCRIPTPATH`/single_end_run_zipped/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Single_end_zipped"); fi

bash "`dirname $SCRIPTPATH`/paired_end_run_zipped/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Paired_end_zipped"); fi

bash "`dirname $SCRIPTPATH`/single_end_run_bwamem/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Single_end_bwa_mem"); fi

bash "`dirname $SCRIPTPATH`/paired_end_run_bwamem/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Paired_end_bwa_mem"); fi

bash "`dirname $SCRIPTPATH`/single_end_run_bwasw/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Single_end_bwa_sw"); fi

bash "`dirname $SCRIPTPATH`/paired_end_run_bwasw/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Paired_end_bwa_sw"); fi

bash "`dirname $SCRIPTPATH`/single_end_run_bwabacktrack/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Single_end_bwa_backtrack"); fi

bash "`dirname $SCRIPTPATH`/paired_end_run_bwabacktrack/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Paired_end_bwa_backtrack"); fi

bash "`dirname $SCRIPTPATH`/single_end_run_trim_galore/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Single_end_trimgalore"); fi

bash "`dirname $SCRIPTPATH`/paired_end_run_trim_galore/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Paired_end_trimgalore"); fi

bash "`dirname $SCRIPTPATH`/single_end_run_segemehl/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Single_end_segemehl"); fi

bash "`dirname $SCRIPTPATH`/paired_end_run_segemehl/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Paired_end_segemehl"); fi


echo -e "\n\n"
echo "Aborted runs:"
for run in "${FAILEDRUNS[@]}"; do
	echo "$run"
done
