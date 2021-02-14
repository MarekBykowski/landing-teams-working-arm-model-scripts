#!/bin/bash -x

HOST_INTERFACE=enp0s3
ARM_INTERFACE=armnet

# Create network bridge and add the host PC network as its interface
#apt-get install bridge-utils
sudo brctl addbr br0
sudo brctl addif br0 $HOST_INTERFACE
sudo ifconfig $HOST_INTERFACE 0.0.0.0
sudo ifconfig br0 up
sudo dhclient br0

# Add the tap interface
sudo ip tuntap add dev $ARM_INTERFACE mode tap user $(whoami)
sudo ifconfig $ARM_INTERFACE 0.0.0.0 promisc up
sudo brctl addif br0 $ARM_INTERFACE

#Add below parameters in run_model.sh:
#
#-C bp.hostbridge.interfaceName=<bridge_interface_name>
#-C bp.smsc_91c111.enabled=1

#in the model /sbin/dhclient eth0 or ifconfig eth 10.0.2.16
