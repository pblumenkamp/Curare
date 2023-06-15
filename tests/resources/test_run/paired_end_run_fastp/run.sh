#!/bin/bash

SCRIPTPATH=`readlink -f $0`
SCRIPTDIR=`dirname $SCRIPTPATH`

#rm -r ${SCRIPTDIR}/output_dir
${SCRIPTDIR}/../../../../bin/curare --samples ${SCRIPTDIR}/samples.tsv --pipeline ${SCRIPTDIR}/pipeline.yaml --output ${SCRIPTDIR}/output_dir -t 4
