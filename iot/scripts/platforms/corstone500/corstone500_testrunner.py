#!/usr/bin/env python2.7

__copyright__ = """
Copyright (c) 2019-2020, Arm Limited and Contributors. All rights reserved.

SPDX-License-Identifier: BSD-3-Clause
"""

import sys
import os
sys.path.append(os.path.join((os.path.dirname(os.path.realpath(__file__))),'..','..','test'))
from testrunner import TestRunner
from corstone500_fvp import A5dsFVP

class A5dsTestRunner(TestRunner):
    def __init__(self):
        TestRunner.__init__(
            self, A5dsFVP
        )

    def setSpecializationArguments(self):
        # corstone500_fvp requires an image_dir argument for its constructor
        # to be able to locate various binaries. Add this as a command-line
        # argument
        self.parser.add_argument("--image_dir", type=str,
            help="Directory containing the Corstone-500 images")

    def parseSpecializationArguments(self, args):
        def tryParseStringArg(arg, argstring):
            if arg is None:
                print("Argument {0} was not specified, but required. exiting...".format(argstring))
                sys.exit(1)
            return arg

        # Set the arguments required for constructing an a5dsFVP object
        # NOTE: the 'key' in FVPWrapperArgs is identical to the named argument
        # 'image_dir' in the a5dsFVP constructor. This is important, given that
        # the FVP Subclass is instantiated by the named arguments present in
        # FVPWrapperArgs via kwargs expansion.
        self.FVPWrapperArgs['image_dir'] = tryParseStringArg(args.image_dir, "--image_dir")
        # The remainder of the arguments for a5dsFVP construction will be
        # provided by the TestRunner base class

    def registerTestSpecifications(self):
        self.registerTest({
            'name'          :   "boot_test",
            'description'   :   "Test A5 Boot",
            'commands'      :   [
                                    ('w', "uname -srmn"),
            ],
            'host_ver_strs' : ["Linux corstone500 5.3.18-yocto-standard armv7l"],
            'host_stop_str' : "Linux corstone500 5.3.18-yocto-standard armv7l"
        })

if __name__ == "__main__":
    A5dsTestRunner()
