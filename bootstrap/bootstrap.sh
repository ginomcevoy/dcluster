#!/bin/bash -x

# Do we have SSH server?
SSH_EXEC=""
if [ -f /sbin/sshd ]; then
    SSH_EXEC="/sbin/sshd"
elif [ -f /usr/sbin/sshd ]; then
    SSH_EXEC="/usr/sbin/sshd"
fi

if [ x${SSH_EXEC} == "x" ]; then
    # No SSH server, try and install it
    # for now, assume yum
    yum install -y openssh-server
    if [ $? -ne 0 ]; then
        >&2 echo "Could not install openssh-server!"
    else
        SSH_EXEC=/sbin/sshd
    fi
fi

if [ x${SSH_EXEC} == "x" ]; then
    >&2 echo "dcluster needs SSH server installed in image, attempt to install it failed!"
    exit 1
fi

# Run SSH server
ssh-keygen -A
${SSH_EXEC} -D 2> /dev/null
