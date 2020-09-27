#!/bin/bash

#
# Try to create a real Docker network for testing.
# See dcluster/infra/networking.py
#
# Giacomo Mc Evoy <giacomo.valenzano@atos.net>
# Atos 2019
#

# Calculate directory local to script
SCRIPTS_DIR="$( cd "$( dirname "$0" )" && pwd )"
PYTHON=$(${SCRIPTS_DIR}/find-python.sh)

cd $SCRIPTS_DIR/..

PYTHONPATH=. $PYTHON -m dcluster.infra.networking
