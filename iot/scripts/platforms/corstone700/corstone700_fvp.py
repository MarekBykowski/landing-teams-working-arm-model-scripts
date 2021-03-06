#!/usr/bin/env python2.7
# Python 2.7 is <required> for fm.debug

__copyright__ = """
Copyright (c) 2019, Arm Limited and Contributors. All rights reserved.

SPDX-License-Identifier: BSD-3-Clause
"""

import sys
import os
corstone700_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join((corstone700_dir),'..','..', 'test'))
from fvp_wrapper import FVPWrapper, TelnetWatcher

""" corstone700_fvp.py
This file contains the corstone700 FVP subclass of the generic FVP wrapper class.
Upon instantiation, telnet watchers are created for each UART exposed by the
FVP, and - using the provided test specification - watchers are set up with their
respective stop and verification conditions.
"""


"""corstone700DefaultConfig
default corstone700 configuration parameters.
Note that these are fully platform dependant, and are only specified in the
following map to provide a clear overview of what the configuration constants
of this script are.
"""
corstone700DefaultConfig = {
    # =============== FVP Parameters ===============
    # Stop condition
    "stop_cnd" : "/OSCI/SystemC: Simulation stopped by user",

    # ROM & Flash loaders
    "se_bootloader"     : "se.trustedBootROMloader.fname",
    "board_flashloader" : "board.flashloader0.fname",
    "es_flashloader"    : "extsys_harness{0}.extsys_flashloader.fname",

    # UART logs
    "host_uart0"     : "host.uart0.out_file",
    "host_uart1"     : "host.uart1.out_file",
    "se_uart"       : "se.uart0.out_file",
    "es_uart"       : "extsys0.uart{0}.out_file",

    # Telnet parameters
    "telnet_host"           : 'localhost',
    "host_telnet_port0"     : 5000,
    "host_telnet_port1"     : 5001,
    "se_telnet_port0"       : 5002,
    "es_telnet_ports"       : [5003,-1,-1,-1],

    # =============== Test parameters ==============
    "linux_login_prompt"    : "corstone700-fvp login:",
    "linux_user"            : "root",
    "linux_shstring"        : "root@corstone700-fvp:~# "
}


""" corstone700DefaultTestspec
Test-specification parameters for corstone700.
Note that this is fully platform-dependant, and only used during the
initialization of corstone700FVP.
"""
corstone700DefaultTestspec = {
    "name"          : None,       # Test name
    "commands"      : [],         # Commands to execute on Host
    "se_bootrom"    : None,       # se boot rom
    "board_flash"   : None,       # Board flash image
    "es_images"     : None,       # External system images []
    "host_stop_str" : None,       # Stop condition string for Host
    "se_stop_str"   : None,       # Stop condition string for SE
    "es_stop_strs"  : [None],     # Stop condition string for ES
    "host_ver_strs" : [],     # Verification strings for Host
    "se_ver_strs"   : [],     # Verification strings for SE
    "es_ver_strs"   : [[]]    # Verification strings for ES
}

class Corstone700FVP(FVPWrapper):
    def __init__(self, testspec, fvp_path, image_dir, usermode, fvp_timeout, stdin):
        FVPWrapper.__init__(
            self,
            fvp_path=fvp_path,
            fvp_name="Corstone-700",
            usermode=usermode,
            work_dir=corstone700_dir,
            fvp_timeout=fvp_timeout,
            testname=testspec['name'],
            stdin=stdin
        )

        self.config = corstone700DefaultConfig
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

        # Host terminal 1 watcher
        self.watchers.append(
            TelnetWatcher(
                name="host1",
                termfile=os.path.join(self.work_dir, self.log_dir, self.testspec['name'] + "_host1.txt"),
                stop_str=None,
                fvp_uart=self.config['host_uart1'],
                port=self.config['host_telnet_port1'],
                sys_stop_str=self.config['stop_cnd'],
            )
        )


        # se watcher
        self.watchers.append(
            TelnetWatcher(
                name="se",
                termfile=os.path.join(self.work_dir, self.log_dir, self.testspec['name'] + "_se.txt"),
                fvp_uart=self.config['se_uart'],
                stop_str=self.testspec['se_stop_str'],
                port=self.config['se_telnet_port0'],
                sys_stop_str=self.config['stop_cnd'],
                verification_strs=self.testspec['se_ver_strs']
            )
        )

        # External system watchers. For now, only ES 0 is created
        self.es_cnt = 1
        for i in range(0, self.es_cnt):
            self.watchers.append(TelnetWatcher(
                    name="es{0}".format(str(i)),
                    termfile=os.path.join(self.work_dir, self.log_dir, self.testspec['name'] +
                                "_es{0}.txt".format(str(i))),
                    fvp_uart=self.config['es_uart'].format(str(i)),
                    stop_str=self.testspec['es_stop_strs'][i],
                    port=self.config['es_telnet_ports'][i],
                    sys_stop_str=self.config['stop_cnd'],
                    verification_strs=self.testspec['es_ver_strs'][i]
                )
            )

    def getModelParameters(self):
        # Assign images to FVP flashloaders
        fvp_params = {}
        fvp_params[self.config['se_bootloader']] = os.path.join(self.image_dir, "se_romfw.bin")
        fvp_params[self.config['board_flashloader']] = os.path.join(self.image_dir, "arm-reference-image-corstone700-fvp.wic.nopt")

        # For now, only external system 0 image is expected
        fvp_params[self.config['es_flashloader'].format(str(0))] = os.path.join(self.image_dir, "es_flashfw.bin")

        return fvp_params

    def getModelData(self):
        # Assign images to FVP data
        fvp_data = {}
        return fvp_data

    def parseTestspec(self, testspec):
        """ Function for parsing a test-specification in line with the arguments
        made available by corstone700DefaultTestspec
        """
        if 'name' not in testspec or 'commands' not in testspec:
            sys.exit(1)

        # Merge user-specified arguments with default test specification
        defaultTestspec = corstone700DefaultTestspec
        defaultTestspec.update(testspec)
        return defaultTestspec
