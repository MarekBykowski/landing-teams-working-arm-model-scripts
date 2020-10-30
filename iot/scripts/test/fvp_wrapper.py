#!/usr/bin/env python2.7
# Python 2.7 is <required> for fm.debug
from __future__ import print_function

__copyright__ = """
Copyright (c) 2019-2020, Arm Limited and Contributors. All rights reserved.

SPDX-License-Identifier: BSD-3-Clause
"""


""" fvp_wrapper.py:
Arm Fast model wrapper.
Provides functionality for executing a fast model together with 'watchers'
to perform unit testing on an fvp.
The FVPWrapper object must be inherited by a target-specific subclass.
This subclass should do any model-specific initialization, as well as
define the watchers (TelnetWatcher) for the FVP.
"""

import os
import signal
import sys
from iris.debug import *
import json
import distutils.spawn
import argparse
import telnetlib
from time import sleep
from threading import Thread
import multiprocessing
import Queue
import time
from subprocess import Popen, PIPE, check_output

from utils import printHeader0, printHeader1

# Default network details for a model running locally a pyIRIS server
g_model_hostname = "localhost"
g_model_port = 7100

g_wait_fvp_ready = 30 #maximum waiting time for the model to be operational (in seconds)
g_wait_fvp_finish = 30 #waiting for the model to terminate and release the TXT log files is expressed in seconds

g_fvp_cmd = ["" , '-I']

#verbose FVP command
#g_fvp_cmd = ["" , '-I' , '-ii' , '-p']

def show_exception_details(e,e_fvp_path,e_fvp_params):

    print("\nError: Exception occured")

    if len(e.message) != 0:
        print("Exception Message: " + e.message)

    print("FVP Info:")
    print("Path: {0}".format(e_fvp_path))
    print("Parameters:")
    print(json.dumps(e_fvp_params, indent=4))


#
# wait_iris_server:
#
# this function supports two modes:
#
# Mode 1: waiting for FVP IRIS server to be ready to receive connections.
# This mode is selected by setting wait_reason to 0
#
# Mode 2: waiting for FVP IRIS server to terminate. This mode is selected by setting wait_reason to a non null value
#
# The function checks every second if the IRIS server port is open until max_wait_time delay expires
#
def wait_iris_server(fvp_process, iris_port, max_wait_time,wait_reason=0):

    netstat_cmd = ["sh", "-c", 'netstat -tpnl 2>/dev/null | egrep -i ":{0}.+{1}" | wc -l'.format(iris_port, fvp_process)]

    i = 0

    while 1:

        i += 1

        ret = check_output(netstat_cmd)

        if int(ret) != 0: #found
            if wait_reason == 0: #waiting for connection
                return True
        else:
            if wait_reason != 0: #waiting for termination
                return True

        if i == max_wait_time:
            return False

        sleep(1)

class TelnetWatcher:
    """ Class for hooking into an ARM telnet session exposed by an FVP. """
    def __init__(self,
                name,
                termfile,
                stop_str,
                sys_stop_str,
                verification_strs = [],
                fvp_uart = None,
                port = None,
                host='localhost',
                ):
        # Watcher configuration
        self.name = name + "_watcher"       # Watcher name

        ''' self.termfile:
            - A text file containing UART logs output in the terminal
            - Created and updated by the FVP
            - Not used for the test strings verifications
        '''
        self.termfile = str(termfile)

        self.stop_str = stop_str            # Test-specific stop string
        self.sys_stop_str = sys_stop_str    # Generic FVP stop string
        self.fvp_uart = fvp_uart            # FVP UART parameter associated with the watcher

        # String which much be present in the UART log after execution
        self.verification_strs = verification_strs

        # Watcher Telnet configuration
        self.host = host
        self.port = port
        self.commandqueue = []

        # Clear file if it is present
        self.clearFile()
        self.termProcess = None

        ''' self.termfilePipe:
            - a file desciptor of a text file with txt_pipe extension
            - contains all the logs displayed in xterm
            - not used for the test strings verifications
        '''
        self.termfilePipe = None

        self.success = True

    def startTerminalPipe(self, fvpname):
        if not distutils.spawn.find_executable("xterm"):
            print("ERROR: xterm not found in path, display telnet contents")
            return
        # Create an intermediate pipe file, which the watcher will print to when
        # a full line has been read.
        termfilePipeName = self.termfile + "_pipe"

        # Remove file if it exists
        try:
            os.remove(termfilePipeName)
        except OSError:
            pass
        self.termfilePipe = open(termfilePipeName, "a+")
        self.termProcess = Popen(['xterm', '-T', self.name, '-e', 'tail', '-f', termfilePipeName])
        sleep(0.1) # Let xterm start before writing to the monitored file

        headerTitle = ("ARM {0} FVP Wrapper".format(fvpname)).center(80)
        termfileHeader = """================================================================================
{0}
This xterm instance will mirror the contents written to the log file:
    {1}
The terminal is read-only, and intended to be used solely for manual monitoring
of a test execution.
================================================================================
""".format(headerTitle, self.termfile)
        self.termfilePipe.write(termfileHeader)
        self.termfilePipe.flush()

    def stopTerminalPipe(self):
        if self.termProcess is not None:
            self.termProcess.kill()
            self.termfilePipe.close()
            os.remove(self.termfilePipe.name)

    def verify(self):
        """ Verifies whether all verification strings are found in the
            watcher log file
        """
        success = True

        if  len(self.verification_strs) != 0:

            with open(self.termfile, "r") as logFile:
                logFile.flush()
                log = logFile.read()
                for string in self.verification_strs:
                    print("{0}: verifying '{1}'... ".format(self.name, string), end='')
                    if string not in log:
                        print("\n{0}: FAIL; '{1}' not found in log".format(self.name, string))
                        success = False
                    else:
                        print("Found!")

        return success

    def addCommand(self, cmdtype, string):
        if cmdtype not in ['r', 'w']:
            print("Unknown command type '{0}'".format(cmdtype))
            print("Commands must be specified as either a read or write command")
            sys.exit(1)
        self.commandqueue.insert(0, (cmdtype, string))

    def getParameters(self):
        if self.fvp_uart is not None:
            return {self.fvp_uart : self.termfile}
        return {}

    def clearFile(self):
        if os.path.isfile(self.termfile):
            # Clear the file
            with open(self.termfile, "w") as f:
                    f.write("")
        else:
            # Create the file
            f = open(self.termfile,"w+")
            f.close()


class FVPWrapper(object):
    """ Controlling Class that wraps around an ARM Fastmodel and controls
    execution.
    This class should be subclassed to configure for a specific FVP model. """
    def __init__(self,
                fvp_path,
                fvp_name,
                work_dir,
                testname,
                fvp_timeout,
                stdin = None,
                usermode = False
                ):

        # Configuration
        self.fvp_path = str(fvp_path)
        self.work_dir = os.path.abspath(work_dir)
        self.log_dir = os.path.join(self.work_dir, "logs")
        self.fvp_timeout = fvp_timeout
        self.fvp_name = fvp_name
        self.watchers = []  # Inheriting class must initialize watchers
        self.testspec = {}  # Inheriting class mus define a test spec

        # FVP Wrapper may be spawned in a child process of some other python
        # script. In this case, to allow for input() within this script,
        # the std input of the parent process must be used (which in turn
        # provides access to the parent terminal stdinput)
        if stdin is not None:
            sys.stdin = os.fdopen(stdin)

        # Check whether log directory exists
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # Asserted only after a complete test run,including end string matching
        self.test_complete = False
        self.test_report = None

        self.monitor_q = multiprocessing.Queue()
        self.stop_all = False
        self.threads = []

        # If userMode is true, the test will display xterm instances for all
        # terminals of the FVP, which will mirror the contents of the terminal
        # log files within the xterm instance.
        # Furthermore, a user will be required to input a character into the
        # python terminal for the test execution to finish, allowing for
        # manual inspection of the terminals
        self.userMode = usermode

        # FVP parameters dictionary.
        # FVP Parameters are derived partly from information from self.watchers,
        # and partly from model-specific configuration as specified by a subclass
        self.fvp_params = {}
        self.fvp_data = {}

    def getModelParameters(self):
        """ The platform specific subclass should implement this function for parsing
        platform-specific model parameters into the fvp_params map. This could be
        parameters specifying ie. images for various flashloaders, initialization
        constants for the FVP etc.
        NOTE: The naming of these arguments must be identical to what is presented
        when an FVP is executed with the --list-params flag
        """
        raise Exception("Model-specific class must implement getModelParameters")

    def getModelData(self):
        raise Exception("Model-specific class must implement getModeldata")

    def load_fvp(self):
        try:
            # Get model specific parameters specified by inheriting class
            self.fvp_params.update(self.getModelParameters())
            self.fvp_data.update(self.getModelData())
            # Get watcher specific model parameters from each watcher
            for watcher in self.watchers:
                self.fvp_params.update(watcher.getParameters())

            print("FVP parameters:")
            print(self.fvp_params)

            print("FVP data:")
            print(self.fvp_data)

            g_fvp_cmd[0] = self.fvp_path

            for param,param_val in self.fvp_params.items() :
                g_fvp_cmd.append("-C")
                g_fvp_cmd.append(param+"="+param_val)

            print("FVP commandline:")
            print(g_fvp_cmd)

            Popen(g_fvp_cmd) #running the FVP with pyIRIS server enabled

            fvp_ready = wait_iris_server(fvp_process=self.fvp_name.lower().replace("-",""),
                                         iris_port=g_model_port,max_wait_time=g_wait_fvp_ready,wait_reason=0)

            if fvp_ready == False:
                raise Exception("FVP not ready to connect")

            # Connect to the model through pyIRIS

            # Using pyIRIS network model to connect to the FVP

            self.fvp = NetworkModel(g_model_hostname, g_model_port)

            cpu = self.fvp.get_cpus()[0]

            for key,value in self.fvp_data.items():
                fop = open(value[:-11], "rb")
                image = bytearray(fop.read())
                location = value[len(value)-10:len(value)]
                cpu.write_memory(int(location,0), image)

        except Exception as e:

            show_exception_details(e,self.fvp_path,self.fvp_params)
            sys.exit(1)

        # Model is now loaded and telnet sessions have been started

    def run_watcher(self, watcher):
        """ Run parallel threaded proccesses that monitors a telnet session
        of the FVP and stops it when the a user specified string is found.
        It returns the pid of the proccess for housekeeping """

        def watcher_loop(queue, watcher):

            # Start telnet session
            tn = telnetlib.Telnet(host=watcher.host, port=watcher.port)

            # Poll the telnet session, reading until a line is received
            getNextCmd = True
            while(True):
                # Attempt to pop a command off of the command stack
                while getNextCmd:
                    try:
                        command = watcher.commandqueue.pop()
                    except IndexError:
                        command = None
                    # Execute all write commands which are in sequence
                    if command and command[0] == 'w':
                        tn.write((command[1] + '\n').encode('utf-8'))
                        getNextCmd = True
                    else:
                        getNextCmd = False

                # Read until a full line has been received or the watcher is
                # signalled to stop
                line = ""
                while(# Stop if a newline character is seen
                    '\n' not in line and
                    # Stop if the global stop signal has been asserted
                    not self.stop_all and
                    # Stop if the string of a 'read' command is found
                    (command[1] not in line if command and command[0] == 'r' else True)):
                    line += tn.read_very_eager().decode('utf-8')

                if watcher.termProcess is not None:
                    # Pipe terminal contents to user-visible terminal if available
                    watcher.termfilePipe.write(line)
                    watcher.termfilePipe.flush()

                if self.stop_all:
                    return

                # Process a 'read' command
                if command and command[0] == 'r' and command[1] in line:
                    getNextCmd = True

                if(watcher.stop_str is not None and watcher.stop_str in line):
                    queue.put("{0}: Found end string \"{1}\"".format(watcher.name, watcher.stop_str))
                    queue.put("{0}: Stopping all other threads...".format(watcher.name))
                    self.test_complete = True
                    self.stop()
                    return

                # Check for the system stop string (ie. FVP stopped by itself)
                if watcher.sys_stop_str in line:
                    self.success = False
                    queue.put("Simulation Ended: \"{0}\"".format(line))
                    self.stop()
                    return

                # Yield
                sleep(0)

        # Run the watcher as a separate thread
        watcher_thread = Thread(target=watcher_loop,
                                args=(self.monitor_q, watcher))
        watcher_thread.setName(watcher.name)
        watcher_thread.start()

        if self.userMode:
            watcher.startTerminalPipe(self.fvp_name)

        return watcher_thread

    def monitor_consume(self):
        """ Read the ouptut of the monitor thread and print the queue entries
        one entry at the time (One line per call) """
        try:
            line = self.monitor_q.get_nowait()
        except Queue.Empty:
            return
        else:
            print(line.rstrip())
            self.monitor_consume()

    def has_stopped(self):
        """Return status of stop flag. True indicated stopped state """
        return self.stop_all

    def start(self):
        # Load the FVP, exposing the Telnet sessions
        self.load_fvp()

        # Start telnet watchers
        for watcher in self.watchers:
            if watcher.port != None:
                self.threads.append(self.run_watcher(watcher))

        # With all watchers hooked into their telnet sessions, the test may
        # commence.
        # To log the FVP output, the fvp is executed in a separate process,
        # assigning stdout for the process to the FVP log file

        self.fvp.run(blocking=False)

        # Start test timer
        self.startTime = time.time()

    def stop(self):
        """ Send stop signal to all threads """
        self.stop_all = True

    def test(self):
        """ Compare each watcher log file with its corresponding verification
            strings.
        """
        for watcher in self.watchers:
            self.success &= watcher.verify()


    def blocking_wait(self):
        """ Block execution flow and wait for one of the watchers to complete """
        try:
            while True:
                for thread in self.threads:
                    self.monitor_consume()
                    if not thread.isAlive():
                        print(("Thread '{0}' finished," +
                        "sending stop signal to all threads...").format(thread.getName()))
                        self.stop()
                        break
                if self.has_stopped():
                    break
                # Check for timeout
                if (time.time() - self.startTime) > self.fvp_timeout:
                    print("ERROR: Timeout reached! ({0} seconds)".format(self.fvp_timeout))
                    self.stop()
                    break


        except KeyboardInterrupt:
            print("User initiated interrupt")
            self.stop()

        # Join all threads
        print("Awaiting all threads to finish...")
        for thread in self.threads:
            print("Joining with thread: " + thread.getName())
            thread.join()
        print("All threads finished")

    def verifyInitialization(self):
        """ Various sanity checks to verify that an inheriting class has
            initialized the FVP correctly
        """
        if len(self.watchers) == 0:
            raise Exception("No watchers were set, aborting...")

    def executeTest(self):
        try:
            self.success = True
            self.verifyInitialization()

            printHeader0("FVP Test: {0}".format(self.testspec['name']))

            # Start the wrapper
            print()
            printHeader1("FVP Execution")
            self.start()

            # Wait for the wrapper to complete
            self.blocking_wait()

            print("Test execution finished, shutting down model...")

            #terminates the model and allows the FVP to release the TXT log files
            self.fvp.release(True)

            fvp_terminated = wait_iris_server(fvp_process=self.fvp_name.lower().replace("-", ""),
                                         iris_port=g_model_port, max_wait_time=g_wait_fvp_finish, wait_reason=1)

            if fvp_terminated == False:
                raise Exception("FVP failed to shutdown")

            print("FVP shutdown successfully")

            if self.success:
                print()
                printHeader1("FVP Test Verification: {0}".format(self.testspec['name']))
                # Test the output of the system only after a full execution
                self.test()

            if self.userMode:
                # Await user input, allowing the terminals to be inspected before
                # finishing the test.
                raw_input("Press enter to continue...")
                # Stop terminal processes and clean up pipe files
                for watcher in self.watchers:
                    watcher.stopTerminalPipe()

            print("\n")
            if self.success:
                printHeader1("FVP Test successfull: {0}".format(self.testspec['name']))
                print('='*80 + "\n\n")
                return 0
            else:
                printHeader1("FVP Test failed: {0}".format(self.testspec['name']))
                print('='*80 + "\n\n")

            return 1

        except Exception as e:

            show_exception_details(e, self.fvp_path, self.fvp_params)
            sys.exit(1)
