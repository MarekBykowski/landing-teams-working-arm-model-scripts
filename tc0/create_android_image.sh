#!/usr/bin/env bash

# Copyright (c) 2020, ARM Limited and Contributors. All rights reserved.
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

set -e

if [ -z "$ANDROID_PRODUCT_OUT" ]
then
      echo "var ANDROID_PRODUCT_OUT is empty"
      exit 1
fi

pushd .

cd $ANDROID_PRODUCT_OUT

IMG=${IMG:-android.img}

size_in_mb() {
	local size_in_bytes
	size_in_bytes=$(wc -c $1)
	size_in_bytes=${size_in_bytes%% *}
	echo $((size_in_bytes / 1024 / 1024 + 1))
}

SYSTEM_IMG=${SYSTEM_IMG:-system.img}
SYSTEM_SIZE=$(size_in_mb ${SYSTEM_IMG})
USERDATA_IMG=${USERDATA_IMG:-userdata.img}
USERDATA_SIZE=$(size_in_mb ${USERDATA_IMG})

IMAGE_LEN=$((SYSTEM_SIZE + USERDATA_SIZE + 4))

# measured in MBytes
PART1_START=1
PART1_END=4
PART2_START=${PART1_END}
PART2_END=$((PART2_START + SYSTEM_SIZE))
PART3_START=${PART2_END}
PART3_END=${IMAGE_LEN}

# We don't want parted to mess with alignment or try to be smart
PARTED="parted -a none --script"

# Create an empty disk image file
dd if=/dev/zero of=$IMG bs=1M count=$IMAGE_LEN

# Create a partition table
$PARTED $IMG unit s mktable msdos

# Create partitions
SEC_PER_MB=$((1024*2))
$PARTED $IMG unit s mkpart p fat32 $((PART1_START * SEC_PER_MB)) $((PART1_END * SEC_PER_MB - 1))
$PARTED $IMG unit s mkpart p ext4 $((PART2_START * SEC_PER_MB)) $((PART2_END * SEC_PER_MB - 1))
$PARTED $IMG unit s mkpart p ext4 $((PART3_START * SEC_PER_MB)) $((PART3_END * SEC_PER_MB - 1))

# Assemble all the images into one final image
dd if=$SYSTEM_IMG of=$IMG bs=1M seek=${PART2_START} conv=notrunc
dd if=$USERDATA_IMG of=$IMG bs=1M seek=${PART3_START} conv=notrunc

popd