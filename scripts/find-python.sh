#!/bin/bash

#
# Finds a usable python executable, tries 3.x first
#
# Giacomo Mc Evoy <giacomo.valenzano@atos.net>
# Atos 2020
#

DEFAULT=$(which python 2> /dev/null)
if [ $? -eq 0 ]; then
  echo $DEFAULT
  exit 0
fi

PYTHON3=$(which python3 2> /dev/null)
if [ $? -eq 0 ]; then
  echo $PYTHON3
  exit 0
fi

PYTHON2=$(which python2 2> /dev/null)
if [ $? -eq 0 ]; then
  echo $PYTHON2
  exit 0
fi

exit 1
