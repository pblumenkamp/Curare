#!/bin/bash

SCRIPTPATH=`readlink -f $0`
SCRIPTDIR=`dirname $SCRIPTPATH`

rm -r ${SCRIPTDIR}/output_dir
${SCRIPTDIR}/../../../../bin/curare start --groups ${SCRIPTDIR}/groups.txt --config ${SCRIPTDIR}/pipeline.yml --output ${SCRIPTDIR}/output_dir -t 2 --cluster-nodes 4 --cluster-command 'qsub -V -b y -pe multislot {cluster.slots} -l {cluster.queue}=1 -l virtual_free={cluster.virtual_free} -N {cluster.name} -terse' --cluster-config-file cluster_config.yml --latency-wait 60
