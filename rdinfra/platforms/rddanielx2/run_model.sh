#!/usr/bin/env bash

# Copyright (c) 2019, ARM Limited and Contributors. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# Neither the name of ARM nor the names of its contributors may be used
# to endorse or promote products derived from this software without specific
# prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Set your ARMLMD_LICENSE_FILE License path for FVP licenses before running
# this script.

NORMAL_FONT="\e[0m"
RED_FONT="\e[31;1m"
GREEN_FONT="\e[32;1m"
YELLOW_FONT="\e[33;1m"
ROOTDIR="../../../../output/rddanielx2"
OUTDIR=${ROOTDIR}/rddaniel
MODEL_TYPE="rddanielx2"
MODEL_PARAMS=""
FS_TYPE=""
TAP_INTERFACE=""
AUTOMATE="false"

source $PWD/../../../sgi/sgi_common_util.sh

# Check that a path to the model has been provided
if [ ! -e "$MODEL" ]; then
	#if no model path has been provided, assign a default path
	MODEL="../../../../fastmodel/refinfra/models/Linux64_GCC-4.9/FVP_RD_Daniel_2XLR"
	if [ ! -f "$MODEL" ]; then
		echo "ERROR: you should set variable MODEL to point to a valid " \
		     "RD-Daniel model binary, currently it is set to \"$MODEL\""
		exit 1
	fi
fi

#Path to the binary models
PATH_TO_MODEL=$(dirname "${MODEL}")

if [ $# -eq 0 ]; then
	echo -e "$YELLOW_FONT Warning!!!!!: Continuing with default : -f busybox" >&2
	echo -e "$YELLOW_FONT Use for more option  ${0##*/} -h|-- help $NORMAL_FONT" >&2
	FS_TYPE="busybox";
	NTW_ENABLE="false";
	VIRT_IMG="false";
	EXTRA_MODEL_PARAMS="";
    VIRTIO_NET="false";
fi

# Display usage message and exit
function usage_help {
	echo -e "$GREEN_FONT usage: ${0##*/} -n <interface_name> -f <fs_type> -v <virtio_image_path> -d <sata_image_path> -a <extra_model_params>" >&2
	echo -e "$GREEN_FONT fs_type = $RED_FONT busybox $NORMAL_FONT" >&2
	echo -e "$GREEN_FONT network_enabled = $RED_FONT true $GREEN_FONT or $RED_FONT false $NORMAL_FONT" >&2
	echo -e "$GREEN_FONT virtio_imag_path = Please input virtio image path $NORMAL_FONT" >&2
	echo -e "$GREEN_FONT sata_image_path = Please input sata disk image path $NORMAL_FONT" >&2
	echo -e "$GREEN_FONT extra_model_params = Input additional model parameters $NORMAL_FONT" >&2
    echo -e "$GREEN_FONT smscnet = Use SMSC91c111 network interface instead of Virtio Net $NORMAL_FONT" >&2
}

while test $# -gt 0; do
	case "$1" in
		-h|--help)
			usage_help
			exit 1
			;;
		-f)
			shift
			if test $# -gt 0; then
				FS_TYPE=$1
			fi
			shift
			;;
		-n)
			shift
			if test $# -gt 0; then
				NTW_ENABLE=$1
			fi
			shift
			;;
		-v)
			shift
			if test $# -gt 0; then
				VIRTIO_IMAGE_PATH=$1
			fi
			shift
			;;
		-d)
			shift
			if test $# -gt 0; then
				SATADISK_IMAGE_PATH=$1
			fi
			shift
			;;
		-a)
			shift
			if test $# -gt 0; then
				EXTRA_MODEL_PARAMS=$1
			fi
			shift
			;;
		-smscnet)
			shift
			if test $# -gt 0; then
				VIRTIO_NET="false"
			fi
			shift
			;;
		-j)
			shift
			if test $# -gt 0; then
				AUTOMATE=$1
				MODEL_PARAMS="$MODEL_PARAMS \
						-C css0.scp.terminal_uart_aon.start_telnet=0 \
						-C css0.mcp.terminal_uart0.start_telnet=0 \
						-C css0.mcp.terminal_uart1.start_telnet=0 \
						-C css0.terminal_uart_ap.start_telnet=0 \
						-C css0.terminal_uart1_ap.start_telnet=0 \
						-C soc0.terminal_s0.start_telnet=0 \
						-C soc0.terminal_s1.start_telnet=0 \
						-C soc0.terminal_mcp.start_telnet=0 \
						-C board0.terminal_0.start_telnet=0 \
						-C board0.terminal_1.start_telnet=0 \
						-C css0.pl011_uart1_ap.out_file="ap-uart1"  \
						-C soc0.pl011_uart_mcp.out_file="soc-mcp-uart0" \
						-C css0.mcp.pl011_uart1_mcp.out_file="css-mcp_uart1" \
						-C css0.mcp.pl011_uart0_mcp.out_file="css-mcp_uart0" \
						-C board0.pl011_uart0.out_file="board-uart0" \
						-C board0.pl011_uart1.out_file="board-uart1"
						-C css1.scp.terminal_uart_aon.start_telnet=0 \
						-C css1.mcp.terminal_uart0.start_telnet=0 \
						-C css1.mcp.terminal_uart1.start_telnet=0 \
						-C css1.terminal_uart_ap.start_telnet=0 \
						-C css1.terminal_uart1_ap.start_telnet=0 \
						-C soc1.terminal_s0.start_telnet=0 \
						-C soc1.terminal_s1.start_telnet=0 \
						-C soc1.terminal_mcp.start_telnet=0 \
						-C board1.terminal_0.start_telnet=0 \
						-C board1.terminal_1.start_telnet=0 \
						-C css1.pl011_uart1_ap.out_file="ap-uart1_1"  \
						-C soc1.pl011_uart_mcp.out_file="soc-mcp-uart0_1" \
						-C css1.mcp.pl011_uart1_mcp.out_file="css-mcp_uart1_1" \
						-C css1.mcp.pl011_uart0_mcp.out_file="css-mcp_uart0_1" \
						-C board1.pl011_uart0.out_file="board-uart0_1" \
						-C board1.pl011_uart1.out_file="board-uart1_1""
			fi
			shift
			;;
		-p)
			shift
			shift
			;;
		*)
			usage_help
			exit 1
			;;
esac
done

if [[ -z $NTW_ENABLE ]]; then
	echo -e "$RED_FONT Continue with <network_enabled> as false !!! $NORMAL_FONT" >&2
	NTW_ENABLE="false";
fi

if [ ${NTW_ENABLE,,} == "true" ]; then
	find_tap_interface
	if [[ -z $TAP_INTERFACE ]]; then
		echo -e "$YELLOW_FONT Please input a unique bridge interface name for network setup $NORMAL_FONT" >&2
		read TAP_INTERFACE
		if [[ -z $TAP_INTERFACE ]]; then
			echo -e "$RED_FONT network interface name is empty $NORMAL_FONT" >&2
			exit 1;
		fi
	fi
fi

if [ ${NTW_ENABLE,,} != "true" ] && [ ${NTW_ENABLE,,} != "false" ]; then
	echo -e "$RED_FONT Unsupported <network_enabled> selected  $NORMAL_FONT" >&2
	usage_help
	exit 1;
fi

if [[ -z $BL1_IMAGE ]]; then
	echo -e "$RED_FONT Continue with <BL1_IMAGE> as tf-bl1.bin !!! $NORMAL_FONT" >&2
	BL1_IMAGE="tf-bl1.bin";
fi

if [[ -z $FIP_IMAGE ]]; then
	echo -e "$RED_FONT Continue with <FIP_IMAGE> as fip-uefi.bin !!! $NORMAL_FONT" >&2
	FIP_IMAGE="fip-uefi.bin";
fi

if [[ -n "$VIRTIO_IMAGE_PATH" ]]; then
	MODEL_PARAMS="$MODEL_PARAMS \
			-C board0.virtioblockdevice.image_path=${VIRTIO_IMAGE_PATH} \
			-C board1.virtioblockdevice.image_path=${VIRTIO_IMAGE_PATH}"
fi

if [[ -n "$SATADISK_IMAGE_PATH" ]]; then
	MODEL_PARAMS="$MODEL_PARAMS \
			-C pci0.ahci.ahci.image_path="${SATADISK_IMAGE_PATH}" \
			-C pci1.ahci.ahci.image_path="${SATADISK_IMAGE_PATH}""
fi

#For distribution installation and boot, ensure that the virtio devices
#behind the PCIe RC are not enumerated.
if [[ ! -z $FS_TYPE ]] && [ ${FS_TYPE,,} == "distro" ]; then
	MODEL_PARAMS="$MODEL_PARAMS \
		-C pci0.pcidevice0.bus=0xFF \
		-C pci0.pcidevice1.bus=0xFF \
		-C pci1.pcidevice0.bus=0xFF \
		-C pci1.pcidevice1.bus=0xFF"
fi

mkdir -p ./$MODEL_TYPE

if [[ ${NTW_ENABLE,,} == "true" && ${VIRTIO_NET} == "false" ]]; then
	MODEL_PARAMS="$MODEL_PARAMS \
		   -C board0.hostbridge.interfaceName="$TAP_INTERFACE" \
		   -C board0.smsc_91c111.enabled=1 \
		   -C board1.hostbridge.interfaceName="$TAP_INTERFACE" \
		   -C board1.smsc_91c111.enabled=1"
elif [ ${NTW_ENABLE,,} == "true" ]; then
	MODEL_PARAMS="$MODEL_PARAMS \
		-C board0.virtio_net.hostbridge.interfaceName="$TAP_INTERFACE" \
		-C board0.virtio_net.enabled=1 \
		-C board0.virtio_net.transport="legacy" \
		-C board1.virtio_net.hostbridge.interfaceName="$TAP_INTERFACE" \
		-C board1.virtio_net.enabled=1 \
		-C board1.virtio_net.transport="legacy" "
fi

#check whether crypto plugin exists
if [ -e $PATH_TO_MODEL_ROOT/plugins/Linux64_GCC-4.9/Crypto.so ]; then
	MODEL_PARAMS="$MODEL_PARAMS \
		   --plugin $PATH_TO_MODEL_ROOT/plugins/Linux64_GCC-4.9/Crypto.so"
fi

echo "NOR1 flash image: $PWD/nor1_flash.img"
create_nor_flash_image "$PWD/nor1_flash.img"
echo "NOR2 flash image: $PWD/nor2_flash.img"
create_nor_flash_image "$PWD/nor2_flash.img"
echo "NOR1 flash image: $PWD/nor1_flash_1.img"
create_nor_flash_image "$PWD/nor1_flash_1.img"
echo "NOR2 flash image: $PWD/nor2_flash_1.img"
create_nor_flash_image "$PWD/nor2_flash_1.img"

echo
echo "Starting model "$MODEL_TYPE
echo "  MODEL_PARAMS = "$MODEL_PARAMS
echo "  EXTRA_PARAMS = "$EXTRA_MODEL_PARAMS
echo "  UART Log     = "$PWD/${MODEL_TYPE,,}/${UART0_ARMTF_OUTPUT_FILE_NAME}
echo

# print the model version.
${MODEL} --version
export FASTSIM_CMN600_INTERNAL_RNSAM=1

PARAMS=" \
	-C css0.cmn_rhodes.mesh_config_file=$PATH_TO_MODEL/rhodes_daniel_cfgxlr.yml \
	-C css0.cmn_rhodes.force_on_from_start=1 \
	--data css0.scp.armcortexm7ct=$OUTDIR/scp_ramfw.bin@0x0BD80000 \
	-C css0.mcp.ROMloader.fname=$OUTDIR/mcp_romfw.bin \
	-C css0.scp.ROMloader.fname=$OUTDIR/scp_romfw.bin \
	-C css0.trustedBootROMloader.fname=$OUTDIR/$BL1_IMAGE \
	-C board0.flashloader0.fname=$OUTDIR/$FIP_IMAGE \
	-C board0.flashloader1.fname=$PWD/nor1_flash.img \
	-C board0.flashloader1.fnameWrite=$PWD/nor1_flash.img \
	-C board0.flashloader2.fname=$PWD/nor2_flash.img \
	-C board0.flashloader2.fnameWrite=$PWD/nor2_flash.img \
	-S -R \
	-C css0.scp.pl011_uart_scp.out_file=${MODEL_TYPE,,}/${UART0_SCP_OUTPUT_FILE_NAME} \
	-C css0.pl011_uart_ap.out_file=${MODEL_TYPE,,}/${UART0_CONSOLE_OUTPUT_FILE_NAME} \
	-C soc0.pl011_uart_mcp.out_file=${MODEL_TYPE,,}/${UART0_MCP_OUTPUT_FILE_NAME} \
	-C soc0.pl011_uart0.out_file=${MODEL_TYPE,,}/${UART0_ARMTF_OUTPUT_FILE_NAME} \
	-C soc0.pl011_uart0.unbuffered_output=1 \
	-C soc0.pl011_uart1.out_file=${MODEL_TYPE,,}/${UART1_MM_OUTPUT_FILE_NAME} \
	-C soc0.pl011_uart1.unbuffered_output=1 \
	-C css0.pl011_uart_ap.unbuffered_output=1 \

	-C css1.cmn_rhodes.mesh_config_file=$PATH_TO_MODEL/rhodes_daniel_cfgxlr.yml \
	-C css1.cmn_rhodes.force_on_from_start=1 \
	--data css1.scp.armcortexm7ct=$OUTDIR/scp_ramfw.bin@0x0BD80000 \
	-C css1.mcp.ROMloader.fname=$OUTDIR/mcp_romfw.bin \
	-C css1.scp.ROMloader.fname=$OUTDIR/scp_romfw.bin \
	-C css1.trustedBootROMloader.fname=$OUTDIR/$BL1_IMAGE \
	-C board1.flashloader0.fname=$OUTDIR/$FIP_IMAGE \
	-C board1.flashloader1.fname=$PWD/nor1_flash_1.img \
	-C board1.flashloader1.fnameWrite=$PWD/nor1_flash_1.img \
	-C board1.flashloader2.fname=$PWD/nor2_flash_1.img \
	-C board1.flashloader2.fnameWrite=$PWD/nor2_flash_1.img \
	-S -R \
	-C css1.scp.pl011_uart_scp.out_file=${MODEL_TYPE,,}/${UART0_SCP_OUTPUT_FILE_NAME}_1 \
	-C css1.pl011_uart_ap.out_file=${MODEL_TYPE,,}/${UART0_CONSOLE_OUTPUT_FILE_NAME}_1 \
	-C soc1.pl011_uart_mcp.out_file=${MODEL_TYPE,,}/${UART0_MCP_OUTPUT_FILE_NAME}_1 \
	-C soc1.pl011_uart0.out_file=${MODEL_TYPE,,}/${UART0_ARMTF_OUTPUT_FILE_NAME}_1 \
	-C soc1.pl011_uart0.unbuffered_output=1 \
	-C soc1.pl011_uart1.out_file=${MODEL_TYPE,,}/${UART1_MM_OUTPUT_FILE_NAME}_1 \
	-C soc1.pl011_uart1.unbuffered_output=1 \
	-C css1.pl011_uart_ap.unbuffered_output=1 \
	${MODEL_PARAMS} \
	${EXTRA_MODEL_PARAMS}"

if [ "$AUTOMATE" == "true" ] ; then
	${MODEL} $PARAMS ${MODEL_PARAMS} ${EXTRA_MODEL_PARAMS} 2>&1 &
else
	${MODEL} $PARAMS ${MODEL_PARAMS} ${EXTRA_MODEL_PARAMS} 2>&1
fi
if [ "$?" == "0" ] ; then
	echo "Model launched with pid: "$!
	export MODEL_PID=$!
else
	echo "Failed to launch the model"
	export MODEL_PID=0
fi
