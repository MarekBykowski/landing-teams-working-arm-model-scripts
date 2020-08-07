#!/usr/bin/env python2.7

__copyright__ = """
Copyright (c) 2019, Arm Limited and Contributors. All rights reserved.

SPDX-License-Identifier: BSD-3-Clause
"""

import sys
import os
sys.path.append(os.path.join((os.path.dirname(os.path.realpath(__file__))),'..','..','test'))
from testrunner import TestRunner
from corstone700_fvp import Corstone700FVP

class Corstone700TestRunner(TestRunner):
    def __init__(self):
        TestRunner.__init__(
            self, Corstone700FVP
        )

    def setSpecializationArguments(self):
        # corstone700_fvp (Corstone700FVP) requires an image_dir argument for its constructor
        # to be able to locate various binaries. Add this as a command-line
        # argument
        self.parser.add_argument("--image_dir", type=str,
            help="Directory containing the corstone700 images")

    def parseSpecializationArguments(self, args):
        def tryParseStringArg(arg, argstring):
            if arg is None:
                print("Argument {0} was not specified, but required. exiting...".format(argstring))
                sys.exit(1)
            return arg

        # Set the arguments required for constructing an corstone700FVP object
        # NOTE: the 'key' in FVPWrapperArgs is identical to the named argument
        # 'image_dir' in the corstone700FVP constructor. This is important, given that
        # the FVP Subclass is instantiated by the named arguments present in
        # FVPWrapperArgs via kwargs expansion.
        self.FVPWrapperArgs['image_dir'] = tryParseStringArg(args.image_dir, "--image_dir")
        # The remainder of the arguments for corstone700FVP construction will be
        # provided by the TestRunner base class

    def registerTestSpecifications(self):
        # Test external system boot
        self.registerTest({
            'name' : "es_boot",
            'description'   :   "Test external system boot",
            'commands'      :   [
                                    ('w', "cd /usr/bin/"),
                                    ('r', "/usr/bin#"),
                                    ('w', "./test-app 1"),
            ],
            'es_stop_strs'  :   ["Running RTX RTOS"],
            'es_ver_strs'   :   [
                                    [# ES 0:
                                    "External System Cortex-M3 Processor",
                                    "Running RTX RTOS"
                                    ]
                                ]
        })

        # Test external system MHUs
        self.registerTest({
            'name'          :   "es_mhu_test",
            'description'   :   "Test ES <=> (host | SE) MHU devices",
            'commands'      :   [
                                    ('w', "cd /usr/bin/"),
                                    ('r', "/usr/bin#"),
                                    ('w', "./test-app 2"),
            ],
            'es_stop_strs' : ["Received 'abcdf10' From SE MHU1"],
            'se_ver_strs'   :   ["MHUv2: Message from 'MHU0_ES0': 0xabcdf01",
                                 "MHUv2: Message from 'MHU1_ES0': 0xabcdf01"],
            'host_ver_strs' : ["Received abcdf00 from es0mhu0",
                               "Received abcdf00 from es0mhu1"],
            'es_ver_strs'   : [["Received 'abcdef1' From Host MHU0",
                                "Received 'abcdef2' From Host MHU0",
                                "Received 'abcdf10' From SE MHU0",
                                "Received 'abcdef1' From Host MHU1",
                                "Received 'abcdef2' From Host MHU1",
                                "Received 'abcdf10' From SE MHU1"]]
        })

       # Test se MHU
        self.registerTest({
            'name'          :   "se_mhu_test",
            'description'   :   "Test  BP <=> Host MHU device",
            'commands'      :   [
                                    ('w', "cd /usr/bin/"),
                                    ('r', "/usr/bin#"),
                                    ('w', "./test-app 3"),
            ],
            'host_stop_str' : "Received abcdf00 from boot processor",
            'se_ver_strs'   :   ["MHUv2: Message from 'MHU_NS': 0xabcdef1"],
            'host_ver_strs' : ["Received abcdf00 from boot processor"],
        })

        # Test REFCLK and interrupt router
        self.registerTest({
            'name'          :   "se_timer_test",
            'description'   :   "Test REFCLK timer, Interrupt Router and Collator",
            'commands'      :   [
                                    ('w', "cd /usr/bin/"),
                                    ('r', "/usr/bin#"),
                                    ('w', "./test-app 4"),
            ],
            'se_stop_str' : "Timer callback executed",
            'se_ver_strs'   :   ["Timer started", "Timer callback executed"],
            'host_ver_strs' : ["Sent timer test command to boot processor"],
        })

if __name__ == "__main__":
    Corstone700TestRunner()
