#!usr/bin/env python

__copyright__ = """
Copyright (c) 2019, Arm Limited and Contributors. All rights reserved.

SPDX-License-Identifier: BSD-3-Clause
"""

""" Testselector
This script will query all platforms within the 'platforms/' folder for their
available tests ${platform}_testrunner.py script and present options to run these
through a command-line menu.

The testselector may be run with additional arguments for each platform.
These arguments should be the required arguments for the FVP wrappers of a given
platform. Ie. an argument an path for the FVP should be specified.

As an example, the following are needed to execute the Corstone700 testrunner:
python am_ci/scripts/testselector.py --corstone700 "--image_dir ${OUTDIR} --fvp ${BASEDIR}/FVP_Corstone-700.so"

These arguments will then be added to the execution of the Corstone700 testrunner script.
"""

import sys
import os
import json
import re
import subprocess
import argparse

from consolemenu import *
from consolemenu.items import *

pwd = os.path.dirname(os.path.realpath(__file__))

# Index the available platforms in the 'platform/' folder
# The following variable will be a mapping between the available platforms
# and additional argument strings to pass to the given platform's testrunner
# script.
platforms = {}
platforms_dir = os.path.join(pwd, '..', 'platforms')
for platform in [dI for dI in os.listdir(platforms_dir) if os.path.isdir(os.path.join(platforms_dir ,dI))]:
    platforms[platform] = None

# For each platform, additional arguments for executing its respective
# testrunner may be provided. these should be provided as a single string
# for each platform
parser = argparse.ArgumentParser(description="ARM FVP Unit Test Selector")
for platform in platforms:
    parser.add_argument("--{0}".format(platform),
        help="Additional arguments for the testrunner of the {0} platform.".format(platform) +
            " Shall be formatted as a single string (Eg. \"--foo \\\"bar\\\" -a\")",
                required=False, type=str, default = None)
args = parser.parse_args()
for platform, argstring in (vars(args)).iteritems():
    platforms[platform] =  argstring

# ==============================================================================

# The test menu will prompt the user to generate a test run configuration
# This run configuration functor is stored to the following variable,
# which will be executed when the menu exits
queuedTest = None

testsForPlatforms = {}
for platform in platforms:
    try:
        testrunnerpath = os.path.join(platforms_dir, platform,platform + "_testrunner.py")
        if not os.path.isfile(testrunnerpath):
            print("Testrunner file for platform '{0}' was not found".format(platform))
            print("Expected file: {0}".format(testrunnerpath))
            sys.exit(1)

        jsonString = os.popen(
            "python {0} --list".format(testrunnerpath)).read()
        testmap = json.loads(jsonString)
        testsForPlatforms[platform] = testmap
    except:
        print("Could not parse json string from testrunner")
        sys.exit(1)

# Create main menu object
menu = ConsoleMenu(title="ARM FVP Unit Test Runner",
    subtitle="Select Platform")

# Function for creating menu entries which allows the user to specify
# whether to run a specific test in user-mode or not.
def createRuntestMenu(testname = None):
    runTest = False if testname is None else True

    subtitle="""Run {0} in usermode?
  |  In usermode, the test will display xterm instances for all
  |  terminals of the FVP, which will mirror the contents of the
  |  terminal log files within the xterm instance. Terminals are
  |  read-only.""".format(testname if testname is not None else "")

    runtest_submenu = ConsoleMenu(title="ARM FVP Unit Test Runner", subtitle=subtitle)
    # Selecting whether to run in usermode is a leaf-node in the menu navigation
    # tree. These are created as 'FunctionItem's which, upon selection, will
    # execute a registered function.
    runWithUsermode_item = FunctionItem("yes",
        function=testRunnerGenerator(usermode=True, testname=testname,
        runTest=runTest, runAll=not runTest),should_exit=True)
    runWithoutUsermode_item = FunctionItem("no",
        function=testRunnerGenerator(usermode=False, testname=testname,
        runTest=runTest, runAll=not runTest),should_exit=True)
    runtest_submenu.append_item(runWithUsermode_item)
    runtest_submenu.append_item(runWithoutUsermode_item)

    return runtest_submenu

# Add submenu for each platform and its tests
for platform, tests in testsForPlatforms.iteritems():
    # Function which returns a lambda that will, upon execution, instantiate
    # a given test speficiation, as per how the menu was navigated to reach the
    # function
    def testRunnerGenerator(usermode, testname = None, runTest = None, runAll = False):
        testrunnerpath = os.path.join(platforms_dir, platform,platform + "_testrunner.py")
        if runAll:
            testarg = "--runAll"
        else:
            testarg = "--runTest  {0}".format(testname)

        platform_args = platforms[platform]
        platform_args = "" if platform_args is None else platform_args

        # setQueuedTest will return a lambda which upon execution assigns
        # a platform-specific execution of a given test for a given platform
        # to the queuedTest variable. The subsequent execution of queuedTest
        # will then execute the subprocess.Popen command.
        def setQueuedTest():
            global queuedTest
            # Upon execution, the global 'queuedTest' variable will be set
            # according to the menu traversal that led to this option
            queuedTest = lambda : subprocess.Popen(
                "python {0} {1} {2} {3}".format(testrunnerpath,
                testarg,
                platform_args,
                "" if usermode is False else "--usermode"), shell=True).wait()

        return setQueuedTest

    # Add submenu for platform
    arg_info = "Additional arguments: \n" + json.dumps(platforms[platform], indent=4)
    platform_submenu = ConsoleMenu(title="ARM FVP Unit Test Runner", subtitle=
        "{0} Unit Tests".format(platform), prologue_text=arg_info)
    platform_submenu_item = SubmenuItem(platform, platform_submenu, menu=menu, should_exit=True)
    menu.append_item(platform_submenu_item)

    # Add a "run all" menu option
    runtest_item = SubmenuItem("Run all tests", createRuntestMenu(), menu=menu, should_exit=True)
    platform_submenu.append_item(runtest_item)

    # Add options for execution of each test
    for k,v in tests.iteritems():
        runtest_item = SubmenuItem("{0}: {1}".format(k,v), createRuntestMenu(k), menu=menu, should_exit=True)
        platform_submenu.append_item(runtest_item)

# The menu structure has now been created, show the menu and await a command
# which will terminate the menu
menu.show()
menu.join()

if queuedTest is not None:
    # Execute the test specification which was generated during menu traversal
    queuedTest()
