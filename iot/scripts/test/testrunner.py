#!/usr/bin/env python2.7
# Python 2.7 is <required> for fm.debug

__copyright__ = """
Copyright (c) 2019-2020, Arm Limited and Contributors. All rights reserved.

SPDX-License-Identifier: BSD-3-Clause
"""

from multiprocessing import Process
import os
import argparse
import functools
import sys
import json

""" class TestRunner
Base class for running tests on an FVP wrapper derived class.
It is expected that a user will implement a platform-specific testrunner class
for each platform-specific fvp wrapper which is created.
The testrunner class helps manage command line arguments for driving an
fvp wrapper as well as managing the registration and execution of test cases
for a given platform.

Default arguments required by TestRunner, shared by all FVP Wrappers:
- --usermode
- --timeout
- --fvp
- --list
- --runTest
- --runAll

requirements on a test-specification from a TestRunner's point of view:
test must contain:
- "name" field
- "description" field
"""

class TestRunner:
    def __init__(self, FVPType):
        #FVPType is a platform-specific object which inherits from FVPWrapper

        self.tests = {}
        self.FVPType = FVPType

        self.parser = argparse.ArgumentParser()
        self.usermode = False

        # Map of keyworded arguments for executing the specialized FVP wrapper
        self.FVPWrapperArgs = {}

        # Set TestRunner generic arguments
        self.parser.add_argument_group('General options')
        self.parser.add_argument("--usermode", dest='usermode', action='store_true',
        help="If in usermode, terminals will be visible to the user."
             " Furthermore, tests will not exit until input has been" +
             " provided by the user (default: %(default)s)")

        self.parser.add_argument("--timeout", dest='timeout', type=int,
        help="FVP Execution timeout in seconds (default: %(default)s)", default=60)

        self.parser.add_argument("--fvp", type=str,
            help="Absolute path to the FVP .so file")

        # Add options for the execution mode of the testrunner.
        # These are mutually exclusive
        self.parser.add_argument("--list", dest='list', action='store_true',
            help="""List registered tests.
                May be passed as the only argument to the script. In this case, the
                platform specific implementation is queried for its registered tests,
                which are then printed as a JSON-formatted string.""",
                default=False, required=False)

        self.parser.add_argument("--runTest", dest='runTest', type=str,
            help="Run specific test. Execute --list to view available tests",
            required = False, default=None)

        self.parser.add_argument("--runAll", dest='runAll', default=False,
            help="Run all registered tests", required = False, action='store_true')

        # Set Specialization-specific arguments
        self.parser.add_argument_group('FVP specific arguments')
        self.setSpecializationArguments()

        # Generic and specialized arguments are now registered, parse arguments
        args = self.parser.parse_args()
        self.parseArguments(args)

        # Parse test specification
        self.registerTestSpecifications()

        # Check for '--list' execution mode
        # This is done before parsing specialization arguments, allowing for
        # viewing the --list of available tests for a given platform without
        # requiring all of the platform-specific arguments to be specified
        if self.list:
            print(self.getTests())
            sys.exit(0)

        # Parse specialization arguments
        self.parseSpecializationArguments(args)

        # Do execution mode
        if self.runSingle is not None:
            self.runTest(self.runSingle)
        elif self.runAll:
            self.runAllTests()

    def runTest(self, testname):
        """ fm.debug may throw a segmentation fault if a model is launched multiple
            times within the same process. This issue also presents itself if the
            model is run as a separate thread but within the same process.
            To ensure proper clean-up between test executions, execute the model
            in a separate process.
        """
        def runModel(stdin, **kwargs):
            sys.exit(self.FVPType(
                stdin=stdin,
                **kwargs).executeTest())

        try:
            testspec = self.tests[testname]
        except KeyError:
            print("Trying to execute unknown test '{0}', aborting...".format(testname))
            sys.exit(1)

        # Generate argument dictionary for FVP executor
        # Note that these are >named< arguments, and expects the naming
        # to be consistent across FVP constructor argument names.
        kwargs = dict({"testspec": testspec}, **self.FVPWrapperArgs)

        # stdin of this process is passed to spawned processed, enabling stdin
        # in child processes, see:
        # https://stackoverflow.com/questions/7489967/python-using-stdin-in-child-process/15766145#15766145
        stdin = sys.stdin.fileno()

        # Start FVP execution in separate process and await test finished
        p = Process(target=runModel, args=[stdin], kwargs=kwargs)
        p.start()
        p.join()

        # Stop test execution if test failed
        if p.exitcode != 0:
            sys.exit(p.exitcode)

    def runAllTests(self):
        for testname, _ in self.tests.iteritems():
            self.runTest(testname)

    def registerTestSpecifications(self):
        print("Subclass did not implement test registration")
        raise BaseException()

    def parseSpecializationArguments(self, args):
        print("Subclass did not implement argument parsing")
        raise BaseException()

    def setSpecializationArguments(self):
        print("Subclass did not implement argument parsing")
        raise BaseException()

    def parseArguments(self, args):
        # Parse generic arguments (arguments for all FVP wrappers)
        self.FVPWrapperArgs['usermode'] = args.usermode
        self.FVPWrapperArgs['fvp_timeout'] = args.timeout
        self.FVPWrapperArgs['fvp_path'] = args.fvp

        def booleanize(arg):
            return True if arg is not None else False

        # Parse arguments specifying the execution mode of the Test runner
        self.list = args.list
        self.runAll = args.runAll
        self.runSingle = args.runTest

        # Test runner execution mode is mutually exclusive
        if not reduce((lambda x,y: x ^ y), [args.list, args.runAll, booleanize(args.runTest)]) :
            if not (args.list and args.runAll and booleanize(args.runTest)):
                # None of the mutually exclusive arguments were provided
                self.parser.print_help()
            else:
                print('--list, --runTest and --runAll are mutually exclusive')
            sys.exit(1)

    def registerTest(self, test):
        if not 'name' in test or not 'description' in test:
            print("Invalid test specification, test must contain" +
                  "'name' and 'description' entries")
            sys.exit(1)
        self.tests[test['name']] = test

    def getTests(self):
        """ Returns a JSON formatted string of tests which have been registered with the
        runner, their names and descriptions"""
        testDescriptions = {}
        for _, test in self.tests.iteritems():
            testDescriptions[test['name']] = test['description']
        return json.dumps(testDescriptions, indent=4)
