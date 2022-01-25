#!/bin/bash

# Usage and input parsing
usage() {
	echo -e "$0 <config>\n"
}

if [ "$#" -ne 1 ]; then
    echo "Illegal number of parameters"
    usage
    exit 1
fi

config=$1

# Complicated invocation that runs the many different Ryu programs that are
# necessary to make running and grading the student code possible.  Assumes
# that this is being run from the VM and that the student's code is checked out
# in the /home/ryu/ directory.
sudo ryu-manager --verbose --observe-links --config-file $config /home/ryu/ryu/ryu/topology/switches.py /home/ryu/ryu/ryu/app/ofctl_rest.py /home/ryu/ryu/ryu/app/rest.py /home/ryu/CN-PRJ2/hw9.py
