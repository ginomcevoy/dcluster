#!/bin/bash

#
# Try to create a real Docker network for testing.
# See dcluster/infra/networking.py
#
# Giacomo Mc Evoy <giacomo.valenzano@atos.net>
# Atos 2019
#

# Calculate directory local to script
BIN_DIR="$( cd "$( dirname "$0" )" && pwd )"

cd $BIN_DIR/..

PYTHONPATH=. python -m dcluster.infra.networking
