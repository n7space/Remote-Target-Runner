#!/usr/bin/python3

import os
import sys
import getopt
from pathlib import Path

import gdb_runner
from libs.GdbServerInvoker import GdbServerInvoker

vConsole = ''
vUart4 = ''
configPath = str(Path(__file__).resolve().parent) + '/Config/taste.cfg'

try :
    binary = sys.argv[1]
except:
    print("Error! SamV71 binary path was not passed to the script!")
    quit()

try:
    opts, args = getopt.getopt(sys.argv[2:],"c:v:u:",["config=","vconsole=","uart"])
except getopt.GetoptError:
    print("Error while parsing arguments.")
    sys.exit(2)

for opt, arg in opts:
    if opt in ("-c", "--config"):
        configPath = arg
    elif opt in ("-v", "--vConsole"):
        vConsole = arg
    elif opt in ("-u", "--uart"):
        vUart4 = arg

gdbRunner = gdb_runner.gdb_runner(configPath, vConsole, vUart4)
gdbRunner.startOnGdb(binary)
gdbRunner.waitToFinishOnGdb()
