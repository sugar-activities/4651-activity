#!/bin/bash

SCRIPT=`readlink -f $0`
SCRIPT_DIR=`dirname $SCRIPT`
cd "$SCRIPT_DIR"

export GVSIG_INITIAL_MEM="45M"
export GVSIG_MAX_MEM="75M"
export GVSIG_MAX_PERM_SIZE="50M"

jarFile=`ls org.gvsig.educa.batovi.mapviewer*.jar`
$JAVA_HOME/bin/java \
  -Xms${GVSIG_INITIAL_MEM} \
	-Xmx${GVSIG_MAX_MEM} \
	-XX:MaxPermSize=${GVSIG_MAX_PERM_SIZE} \
  -jar "$jarFile"
