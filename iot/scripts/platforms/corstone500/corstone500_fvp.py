#!/usr/bin/env python2.7
# Python 2.7 is <required> for fm.debug

__copyright__ = """
Copyright (c) 2019-2020, Arm Limited and Contributors. All rights reserved.

SPDX-License-Identifier: BSD-3-Clause
"""

import sys
import os
a5ds_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join((a5ds_dir),'..','..', 'test'))
from fvp_wrapper import FVPWrapper, TelnetWatcher

""" corstone500_fvp.py
This file contains the Corstone-500 FVP subclass of the generic FVP wrapper class.
Upon instantiation, telnet watchers are created for each UART exposed by the
FVP, and - using the provided test specification - watchers are set up with their
respective stop and verification conditions.
CA5DS has been rebranded to Corstone-500.
"""


"""a5dsDefaultConfig
default Corstone-500 configuration parameters.
Note that these are fully platform dependant, and are only specified in the
following map to provide a clear overview of what the configuration constants
of this script are.
"""
a5dsDefaultConfig = {
    # =============== FVP Parameters ===============
    # Stop condition
    "stop_cnd" : "/OSCI/SystemC: Simulation stopped by user",
    # data
    "host_cpu0" : "css.cluster.cpu0",
    # address1
    "address1" : "0x80000000",
    # Flash loaders
    "board_ROMloader" : "board.flashloader0.fname",
    # UART logs
    "host_uart0"     : "css.uart_0.out_file",

    # Telnet parameters
    "telnet_host"           : 'localhost',
    "host_telnet_port0"     : 5000,

    # =============== Test parameters ==============
    "linux_login_prompt"    : "corstone500 login:",
    "linux_user"            : "root",
    "linux_shstring"        : "root@corstone500:~# "
}


""" a5dsDefaultTestspec
Test-specification parameters for Corstone-500.
Note that this is fully platform-dependant, and only used during the
initialization of a5dsFVP.
"""
a5dsDefaultTestspec = {
    "name"          : None,       # Test name
    "commands"      : [],         # Commands to execute on Host
    "board_flash"   : None,       # Board flash image
    "host_stop_str" : None,       # Stop condition string for Host
    "host_ver_strs" : [],     # Verification strings for Host
}

class A5dsFVP(FVPWrapper):
    def __init__(self, testspec, fvp_path, image_dir, usermode, fvp_timeout, stdin):
        FVPWrapper.__init__(
            self,
            fvp_path=fvp_path,
            fvp_name="corstone500",
            usermode=usermode,
            work_dir=a5ds_dir,
            fvp_timeout=fvp_timeout,
            testname=testspec['name'],
            stdin=stdin
        )

        self.config = a5dsDefaultConfig
        self.testspec = self.parseTestspec(testspec)
        self.image_dir = image_dir

        # Define watchers for each terminal
        # Host terminal 0 watcher
        host0_watcher = TelnetWatcher(
                name="host0",
                termfile=os.path.join(self.work_dir, self.log_dir, self.testspec['name'] + "_host0.txt"),
                stop_str=self.testspec['host_stop_str'],
                fvp_uart=self.config['host_uart0'],
                port=self.config['host_telnet_port0'],
                sys_stop_str=self.config['stop_cnd'],
                verification_strs=self.testspec['host_ver_strs']
            )
        # We define an initial command sequence for host0 which will login
        # and await until a user can enter commands
        host0_watcher.addCommand('r', self.config['linux_login_prompt'])
        host0_watcher.addCommand('w', self.config['linux_user'])
        host0_watcher.addCommand('r', self.config['linux_shstring'])
        # Once the host is logged in, we add the user-provided test commands
        for commandtype, command in self.testspec['commands']:
            host0_watcher.addCommand(commandtype, command)
        self.watchers.append(host0_watcher)


    def getModelParameters(self):
        # Assign images to FVP flashloaders
        fvp_params = {}
        fvp_params[self.config['board_ROMloader']] = os.path.join(self.image_dir, "bl1.bin")
        print(fvp_params)
        return fvp_params

    def getModelData(self):
        # Assign images to FVP flashloaders
        fvp_data = {}
        fvp_data[self.config['host_cpu0']] = os.path.join(self.image_dir, "arm-reference-image-corstone500.wic.nopt" + "@" + self.config['address1'])
        print(fvp_data)
        return fvp_data


    def parseTestspec(self, testspec):
        """ Function for parsing a test-specification in line with the arguments
        made available by a5dsDefaultTestspec
        """
        if 'name' not in testspec or 'commands' not in testspec:
            sys.exit(1)

        # Merge user-specified arguments with default test specification
        defaultTestspec = a5dsDefaultTestspec
        defaultTestspec.update(testspec)
        return defaultTestspec
