#!/bin/bash

#
# Finds default Python2 pytest
#
# Giacomo Mc Evoy <giacomo.valenzano@atos.net>
# Atos 2020
#

MODERN=$(which pytest-2 2> /dev/null)
if [ $? -eq 0 ]; then
  echo $MODERN 
fi

OLD=$(which py.test 2> /dev/null)
if [ $? -eq 0 ]; then
  echo $OLD
fi

exit 1

