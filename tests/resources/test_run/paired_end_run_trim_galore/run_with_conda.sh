#!/bin/bash

SCRIPTPATH=`readlink -f $0`
SCRIPTDIR=`dirname $SCRIPTPATH`

rm -r ${SCRIPTDIR}/output_dir
python3 ${SCRIPTDIR}/../../../../curare/curare.py --samples ${SCRIPTDIR}/samples.tsv --pipeline ${SCRIPTDIR}/pipeline.yml --output ${SCRIPTDIR}/output_dir -t 4 --use-conda --conda-prefix ../../envs/ --latency-wait 10
