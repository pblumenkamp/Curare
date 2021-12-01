#!/usr/bin/env bash

SCRIPTPATH=$(readlink -f "$0")

FAILEDRUNS=()
bash "`dirname $SCRIPTPATH`/single_end_run/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Single_end"); fi

bash "`dirname $SCRIPTPATH`/paired_end_run/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Paired_end"); fi

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

bash "`dirname $SCRIPTPATH`/single_end_run_star/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Single_end_star"); fi

bash "`dirname $SCRIPTPATH`/paired_end_run_star/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Paired_end_star"); fi

bash "`dirname $SCRIPTPATH`/single_end_run_bowtie/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Single_end_bowtie"); fi

bash "`dirname $SCRIPTPATH`/paired_end_run_bowtie/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Paired_end_bowtie"); fi

bash "`dirname $SCRIPTPATH`/single_end_run_zipped_bowtie2/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Single_end_zipped_bowtie2"); fi

bash "`dirname $SCRIPTPATH`/paired_end_run_zipped_bowtie2/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Paired_end_zipped_bowtie2"); fi

bash "`dirname $SCRIPTPATH`/single_end_run_zipped_bwasw/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Single_end_zipped_bwasw"); fi

bash "`dirname $SCRIPTPATH`/paired_end_run_zipped_bwasw/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Paired_end_zipped_bwasw"); fi

bash "`dirname $SCRIPTPATH`/single_end_run_zipped_bwabacktrack/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Single_end_zipped_bwabacktrack"); fi

bash "`dirname $SCRIPTPATH`/paired_end_run_zipped_bwabacktrack/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Paired_end_zipped_bwabacktrack"); fi

bash "`dirname $SCRIPTPATH`/single_end_run_zipped_bwamem/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Single_end_zipped_bwamem"); fi

bash "`dirname $SCRIPTPATH`/paired_end_run_zipped_bwamem/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Paired_end_zipped_bwamem"); fi

bash "`dirname $SCRIPTPATH`/single_end_run_zipped_segemehl/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Single_end_zipped_segemehl"); fi

bash "`dirname $SCRIPTPATH`/paired_end_run_zipped_segemehl/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Paired_end_zipped_segemehl"); fi

bash "`dirname $SCRIPTPATH`/single_end_run_zipped_trimgalore/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Single_end_zipped_trimgalore"); fi

bash "`dirname $SCRIPTPATH`/paired_end_run_zipped_trimgalore/run_with_conda.sh"
if [ $? -ne 0 ]; then FAILEDRUNS+=("Paired_end_zipped_trimgalore"); fi

echo -e "\n\n"
echo "Aborted runs:"
for run in "${FAILEDRUNS[@]}"; do
	echo "$run"
done
