#!/bin/bash

export HOST_INTERFACE=dummy1

model_run() {
	echo s1 $1
	if [[ $1 = "fvp" ]]; then
		BASE_DIR=/home/marek/fvp
		DEPLOY_DIR=${BASE_DIR}/build-poky/tmp-poky/deploy/images/fvp-base

		#export MODEL=/home/marek/ARM/FastModelsPortfolio_11.12/examples/LISA/FVP_Base/Build_Cortex-A53x4/Linux64-Release-GCC-7.3/isim_system
		#export MODEL=/home/marek/ARM/FastModelsPortfolio_11.12/examples/LISA/FVP_Base/Build_AEMv8A-AEMv8A-AEMv8A-AEMv8A-CCN512/Linux64-Release-GCC-7.3/isim_system
		#export MODEL=/home/marek/FVP_Base_Cortex-A73x124/models/Linux64_GCC-6.4/FVP_Base_Cortex-A73x4
		#export MODEL=/home/marek/FVP_ARM_Std_Library/models/Linux64_GCC-6.4/FVP_Base_Cortex-A73x1
		#export MODEL=/home/marek/ARM/Tool-Solutions/hello-world_fast-models/Cortex-A_Armv8-A/system/Linux64-Release-GCC-7.3/isim_system
		export MODEL=/home/marek/FVP_ARM_Std_Library/models/Linux64_GCC-6.4/FVP_Base_Cortex-A53x4
		#export MODEL=/home/marek/FVP_ARM_Std_Library/models/Linux64_GCC-6.4/FVP_MPS2_Cortex-M4
		export IMAGE=$DEPLOY_DIR/Image
		export BL1=$DEPLOY_DIR/bl1-fvp.bin
		export FIP=$DEPLOY_DIR/fip-fvp.bin
		export DISK=$DEPLOY_DIR/core-image-minimal-fvp-base.disk.img
		export DTB=$DEPLOY_DIR/fvp-base-gicv3-psci-custom.dtb
		export NET=1; echo NET=$NET

		# Test if all the SW components are in place
		test -f "$MODEL" || { echo MODEL not set; set FAIL; }
		test -f "$IMAGE" || { echo IMAGE not set; set FAIL; }
		test -f "$BL1" || { echo BL1 not set; set FAIL; }
		test -f "$FIP" || { echo FIP not set; set FAIL; }
		test -f "$DISK" || { echo DISK not set; set FAIL; }
		test -f "$DTB" || { echo DTB not set; set FAIL; }

		# run the model if FAIL not set
		test -v FAIL || { cd /home/marek/repos/landing-teams-working-arm-model-scripts/fvp && ./run_model.sh; }
	elif [[ $1 = "fa" ]]; then
		BASE_DIR=/home/marek/yocto_foundation
		DEPLOY_DIR=${BASE_DIR}/build-poky/tmp-poky/deploy/images/foundation-armv8

		export MODEL=/home/marek/Foundation_Platformpkg/models/Linux64_GCC-6.4/Foundation_Platform
		export IMAGE=${DEPLOY_DIR}/Image
		export BL1=${DEPLOY_DIR}/bl1.bin
		export FIP=${DEPLOY_DIR}/fip.bin
		export DISK=${DEPLOY_DIR}/core-image-minimal-foundation-armv8.disk.img
		export DTB=${DEPLOY_DIR}/foundation-v8-gicv3-psci.dtb

		export NET=1; echo NET=$NET

		# Test if all the SW components are in place
		test -f "$MODEL" || { echo MODEL not set; set FAIL; }
		test -f "$IMAGE" || { echo IMAGE not set; set FAIL; }
		test -f "$BL1" || { echo BL1 not set; set FAIL; }
		test -f "$FIP" || { echo FIP not set; set FAIL; }
		test -f "$DISK" || { echo DISK not set; set FAIL; }
		test -f "$DTB" || { echo DTB not set; set FAIL; }

		# run the model if FAIL not set
		test -v FAIL || { cd /home/marek/repos/landing-teams-working-arm-model-scripts/fvp && ./run_model.sh; }
	elif [[ $1 = "corstone" ]]; then
		MODEL=/home/marek/FVP_Corstone_700/models/Linux64_GCC-6.4/FVP_Corstone-700
		test -f $MODEL || { echo "MODEL not set"; set FAIL; }

		test -v FAIL || {
		cd /home/marek/repos/landing-teams-working-arm-model-scripts/iot
		./run_model.sh $MODEL
		}
	else
		echo "${BASH_SOURCE[0]} fa | fvp | corstone"
	fi


}

model_interface_dummy() {
	sudo modprobe dummy
	sudo ip link add $HOST_INTERFACE type dummy
	sudo ip addr add 192.168.0.30/24 dev $HOST_INTERFACE
	sudo ip link set $HOST_INTERFACE up
}

model_interface_br() {
	ARM_INTERFACE=armnet

	# Create network bridge and add the host PC network as its interface
	#apt-get install bridge-utils
	sudo brctl addbr br0
	sudo brctl addif br0 $HOST_INTERFACE
	sudo ifconfig $HOST_INTERFACE 0.0.0.0
	sudo ifconfig br0 up
	#sudo dhclient br0 -r
	#sudo dhclient br0 -v
	sudo ifconfig br0 192.168.0.30
	echo "$HOST_INTERFACE IP 192.168.0.30"

	# Add the tap interface
	sudo ip tuntap add dev $ARM_INTERFACE mode tap user $(whoami)
	sudo ifconfig $ARM_INTERFACE 0.0.0.0 promisc up
	sudo brctl addif br0 $ARM_INTERFACE

	#Add below parameters in run_model.sh:
	#-C bp.hostbridge.interfaceName=<bridge_interface_name>
	#-C bp.smsc_91c111.enabled=1
	#in the model /sbin/dhclient eth0 or ifconfig eth 10.0.2.16
}

model_interface() {
	echo "Setting network for the MODEL"
	model_interface_dummy
	model_interface_br
}

if [[ $0 != ${BASH_SOURCE[0]} ]]; then
cat << EOC
Sourcing ${BASH_SOURCE[0]} resulted in with:

model_run
model_interface

model_interface() {
echo "Setting network for the MODEL"
model_interface_dummy
model_interface_br
}
EOC
fi
