#!/bin/bash

#
# Remove compiled files to get clean source 
#
# Giacomo Mc Evoy <giacomo.valenzano@atos.net>
# Atos 2020
#

# Calculate directory local to script
BIN_DIR="$( cd "$( dirname "$0" )" && pwd )"

# get a clean source
cd $BIN_DIR/..

# remove all these transient files
find -name '*.pyc' -delete
find -name __pycache__ -delete
rm -rf .pytest_cache
rm -rf build
