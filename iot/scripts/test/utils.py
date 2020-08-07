#!/usr/bin/env python2

__copyright__ = """
Copyright (c) 2019, Arm Limited and Contributors. All rights reserved.

SPDX-License-Identifier: BSD-3-Clause
"""

import math
HEADER_WIDTH = 80

def printHeader1(string):
    eqcnt = (float(HEADER_WIDTH) - 2 - len(string)) / 2
    eql = int(eqcnt if eqcnt.is_integer() else math.floor(eqcnt))
    eqr = int(eqcnt if eqcnt.is_integer() else math.ceil(eqcnt))
    print("{0} {1} {2}".format('='*eql, string, '='*eqr))

def printHeader0(string):
    print('='*HEADER_WIDTH)
    printHeader1(string)
    print('='*HEADER_WIDTH)
