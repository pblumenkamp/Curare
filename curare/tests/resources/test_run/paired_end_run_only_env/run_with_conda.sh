#!/bin/bash

SCRIPTPATH=`readlink -f $0`
SCRIPTDIR=`dirname $SCRIPTPATH`

rm -r ${SCRIPTDIR}/output_dir
python3 ${SCRIPTDIR}/../../../../curare.py --groups ${SCRIPTDIR}/groups.txt --config ${SCRIPTDIR}/pipeline.yml --output ./output_dir --create-conda-envs-only
