#!/bin/bash

# Run tests for dcluster

# Giacomo Mc Evoy <giacomo.valenzano@atos.net>
# Atos 2019

# Calculate directory local to script
BIN_DIR="$( cd "$( dirname "$0" )" && pwd )"

cd $BIN_DIR/..

# get a clean source
find -name '*.pyc' -delete
find -name __pycache__ -delete


MODULE=dcluster

if [ "x$1" == "x--pytest" ]; then
    # with pytest
    PYTHONPATH=. pytest-3 --pyargs $MODULE -v
else
    # with unittest
    PYTHONPATH=. python -m unittest discover $MODULE -v
fi
 
