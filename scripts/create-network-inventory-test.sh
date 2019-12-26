#!/bin/bash

# Try to create a real Docker network AND Ansible inventory for testing

# Giacomo Mc Evoy <giacomo.valenzano@atos.net>
# Atos 2019

# Calculate directory local to script
BIN_DIR="$( cd "$( dirname "$0" )" && pwd )"

cd $BIN_DIR/..

PYTHONPATH=. python -m dcluster.inventory
