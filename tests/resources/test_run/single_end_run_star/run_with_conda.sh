#!/bin/bash

SCRIPTPATH=`readlink -f $0`
SCRIPTDIR=`dirname $SCRIPTPATH`

rm -r ${SCRIPTDIR}/output_dir
python3 ${SCRIPTDIR}/../../../../curare/curare.py --samples ${SCRIPTDIR}/samples.tsv --pipeline ${SCRIPTDIR}/pipeline.yaml --output ${SCRIPTDIR}/output_dir -t 8 --use-conda --conda-prefix ../../envs/ --conda-frontend mamba
