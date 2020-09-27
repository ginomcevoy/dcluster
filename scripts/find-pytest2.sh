#!/bin/bash

#
# Finds suitable Python2 pytest
#
# Giacomo Mc Evoy <giacomo.valenzano@atos.net>
# Atos 2020
#

MODERN=$(which pytest-2 2> /dev/null)
if [ $? -eq 0 ]; then
  echo $MODERN 
  exit 0
fi

OLD=$(which py.test 2> /dev/null)
if [ $? -eq 0 ]; then
  # verify that this is a very old py.test for Python 2
  # instead of the modern py.test for Python 3
  MAJOR=$(py.test /dev/null | head -n 2 | tail -n 1 | cut -d ' ' -f 5 | head -c 1)
  if [ "x${MAJOR}" == "x2" ]; then
    echo $OLD
    exit 0
  fi
fi

exit 1

