#!/bin/bash -x

#
# Build the RPMs our own way
#
# Giacomo Mc Evoy <giacomo.valenzano@atos.net>
# Atos 2019
#
# version: 0.2
#

# calculate directory local to script
SCRIPTS_DIR="$( cd "$( dirname "$0" )" && pwd )"
SRC_HOME_DIR=$SCRIPTS_DIR/..
cd $SRC_HOME_DIR

# start clean
rm -rf build

PYTHON=$(${SCRIPTS_DIR}/find-python.sh)

# get the name of this package
PKG_NAME=$($PYTHON setup.py --name)

# call the default RPM builder
$PYTHON setup.py bdist_rpm

cd build/*/rpm

# save the original SPEC header, it describes versionsing
# delete the rest
SPEC_FILE=SPECS/${PKG_NAME}.spec
cat $SPEC_FILE | head -n 5 > /tmp/${PKG_NAME}.spec
mv /tmp/${PKG_NAME}.spec $SPEC_FILE

# add a line to the header that simplifies the handling of the name change
# from <pkg> to python-<pkg>
echo "%define mod_name ${PKG_NAME}" >> $SPEC_FILE 

# use our custom-made SPEC template, we are keeping the header
cat $SRC_HOME_DIR/${PKG_NAME}.spec.in >> $SPEC_FILE

# add the changelog
cat $SRC_HOME_DIR/${PKG_NAME}.changelog.in >> $SPEC_FILE

# build the RPMs again (python3-*.noarch.rpm)
# running tests
rpmbuild --with tests -ba --define "_topdir $PWD" --verbose $SPEC_FILE

# clean up the old dist RPMs, put our own
rm $SRC_HOME_DIR/dist/*.rpm
cp RPMS/noarch/* SRPMS/* $SRC_HOME_DIR/dist/

# save each SRPM separately for record
HISTORY_DIR=$SRC_HOME_DIR/dist/history
mkdir -p $HISTORY_DIR
cp -f SRPMS/* $HISTORY_DIR/
