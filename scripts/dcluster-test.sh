#!/bin/bash

#
# Run tests for dcluster.
# Add '--pytest' to use pytest if available.
#
# Giacomo Mc Evoy <giacomo.valenzano@atos.net>
# Atos 2019
#

# Calculate directory local to script
BIN_DIR="$( cd "$( dirname "$0" )" && pwd )"

# Check availability
PYTHON2=$(which python2)
PYTEST2=$($BIN_DIR/find-pytest2.sh)

PYTHON3=$(which python3)
PYTEST3=$($BIN_DIR/find-pytest3.sh)

# get a clean source
$BIN_DIR/clean.sh

cd $BIN_DIR/..

# assume dev
export DCLUSTER_DEV=true

MODULE=dcluster

if [ "x$1" == "x--pytest" ]; then
  # with pytest

  # for python2?
  if [ ! -z ${PYTEST2} ]; then
    PYTHONPATH=. ${PYTEST2} --pyargs $MODULE -v
  fi

  # for python3
  if [ ! -z ${PYTEST3} ]; then
    PYTHONPATH=. ${PYTEST3} --pyargs $MODULE -v
  fi

else
  # with unittest
  
  # for python2?
  if [ ! -z ${PYTHON2} ]; then
    PYTHONPATH=. ${PYTHON2} -m unittest discover $MODULE -v
  fi

  # for python3?
  if [ ! -z ${PYTHON3} ]; then
    PYTHONPATH=. ${PYTHON3} -m unittest discover $MODULE -v
  fi
fi
