#!/bin/bash

#
# Finds suitable Python3 pytest
#
# Giacomo Mc Evoy <giacomo.valenzano@atos.net>
# Atos 2020
#

# Prefer py.test from pip3
FROM_PIP=$(which py.test 2> /dev/null)
if [ $? -eq 0 ]; then
  # verify that this is the modern py.test for Python 3
  # instead of a very old py.test for Python 2
  MAJOR=$(py.test /dev/null | head -n 2 | tail -n 1 | cut -d ' ' -f 5 | head -c 1)
  if [ "x${MAJOR}" == "x3" ]; then
    echo $FROM_PIP
    exit 0
  fi 
fi

# Revert to pytest-3 from RPM
FROM_RHEL=$(which pytest-3 2> /dev/null)
if [ $? -eq 0 ]; then
  echo $FROM_RHEL
  exit 0
fi

exit 1
