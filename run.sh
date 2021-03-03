#!/bin/bash

if [[ $1 = "fvp" ]]; then
	BASE_DIR=/home/marek/yocto_foundation
	DEPLOY_DIR=${BASE_DIR}/build-poky/tmp-poky/deploy/images/fvp-base

	#export MODEL=/home/marek/ARM/FastModelsPortfolio_11.12/examples/LISA/FVP_Base/Build_Cortex-A53x4/Linux64-Release-GCC-7.3/isim_system
	#export MODEL=/home/marek/ARM/FastModelsPortfolio_11.12/examples/LISA/FVP_Base/Build_AEMv8A-AEMv8A-AEMv8A-AEMv8A-CCN512/Linux64-Release-GCC-7.3/isim_system
	#export MODEL=/home/marek/FVP_Base_Cortex-A73x124/models/Linux64_GCC-6.4/FVP_Base_Cortex-A73x4
	#export MODEL=/home/marek/FVP_ARM_Std_Library/models/Linux64_GCC-6.4/FVP_Base_Cortex-A73x1
	export MODEL=/home/marek/FVP_ARM_Std_Library/models/Linux64_GCC-6.4/FVP_Base_Cortex-A53x4
	#export MODEL=/home/marek/ARM/Tool-Solutions/hello-world_fast-models/Cortex-A_Armv8-A/system/Linux64-Release-GCC-7.3/isim_system
	export IMAGE=$DEPLOY_DIR/Image
	export BL1=$DEPLOY_DIR/bl1-fvp.bin
	export FIP=$DEPLOY_DIR/fip-fvp.bin
	export DISK=$DEPLOY_DIR/core-image-minimal-fvp-base.disk.img
	export DTB=$DEPLOY_DIR/fvp-base-gicv3-psci-custom.dtb
	export NET=1; echo NET=$NET

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
else
	echo "$0 fa or fvp"
	exit 0
fi

# Test if all the pieces are in place
test -f "$MODEL" || { echo MODEL not set; exit; }
test -f "$IMAGE" || { echo IMAGE not set; exit; }
test -f "$BL1" || { echo BL1 not set; exit; }
test -f "$FIP" || { echo FIP not set; exit; }
test -f "$DISK" || { echo DISK not set; exit; }
test -f "$DTB" || { echo DTB not set; exit; }

cd ./fvp && ./run_model.sh
