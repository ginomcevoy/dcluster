#!/bin/bash

# Run tests for dcluster

# Giacomo Mc Evoy <giacomo.valenzano@atos.net>
# Atos 2019

# Calculate directory local to script
BIN_DIR="$( cd "$( dirname "$0" )" && pwd )"

# Check availability
PYTEST2=$($BIN_DIR/find-pytest2.sh)
TEST_PYTHON3=$(which python3 2> /dev/null)
if [ $? -eq 0 ]; then
  WITH_PYTHON3='y'
fi

# get a clean source
$BIN_DIR/clean.sh

cd $BIN_DIR/..

# assume dev
export DCLUSTER_DEV=true

MODULE=dcluster

if [ "x$1" == "x--pytest" ]; then
    # with pytest
    PYTHONPATH=. $PYTEST2 --pyargs $MODULE -v
    if [ x$WITH_PYTHON3 == 'xy' ]; then
    	PYTHONPATH=. pytest-3 --pyargs $MODULE -v
    fi
else
    # with unittest
    PYTHONPATH=. python2 -m unittest discover $MODULE -v
    if [ x$WITH_PYTHON3 == 'xy' ]; then
    	PYTHONPATH=. python3 -m unittest discover $MODULE -v
    fi
fi

