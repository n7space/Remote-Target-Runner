#!/usr/bin/python3

import os
import sys

import gdb_runner
from libs.GdbServerInvoker import GdbServerInvoker

try :
    binary = sys.argv[1]
except:
    print("Error! SamV71 binary path was not passed to the script!")
    quit()

try : 
    vConsole = sys.argv[2]
except:
    print("Using default console virtual tty: (/tmp/vConsole) ")
    vConsole = "vConsole"

try :
    vUart4 = sys.argv[3]
except:
    print("Using default uart4 virtual tty: (/tmp/vUart4)")
    vUart4 = "vUart4"

try: 
    configPath = sys.argv[4]
except:
    print("Using default config: Config/taste.cfg")
    configPath ="Config/taste.cfg"

gdbRunner = gdb_runner.gdb_runner(configPath, vConsole, vUart4)
gdbRunner.startOnGdb(binary)
gdbRunner.waitToFinishOnGdb()
