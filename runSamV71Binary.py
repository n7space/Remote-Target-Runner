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
    consoleVTTY = sys.argv[2]
except:
    print("Using default console virtual tty: (/tmp/vConsole) ")
    consoleVTTY = "/tmp/vConsole"

try :
    uart4VTTY = sys.argv[3]
except:
    print("Using default uart4 virtual tty: (/tmp/vUart4)")
    uart4VTTY = "/tmp/vUart4"

sshAddress = os.environ['TASTE_RASPI_ADDRESS']
sshPort = os.environ['TASTE_RASPI_PORT']
sshPassword = os.environ['TASTE_RASPI_PASSWORD']
sshUser = os.environ['TASTE_RASPI_USER']

gdbServerAddress = sshAddress
gdbServerUserName = sshUser
gdbServerPassword = sshPassword
gdbServerPath = "/usr/local/bin/openocd"
gdbServerArgs = "-f /usr/local/share/openocd/scripts/interface/cmsis-dap.cfg -f /usr/local/share/openocd/scripts/board/atmel_samv71_xplained_ultra.cfg -f /home/pi/broadcastOpenocd.cfg"
gdbServerVerbose = True

gdbAddress = sshAddress+":"+sshPort
gdbPath = "gdb-multiarch"
gdbVerbose = True

consoleIoHandlerID = 4
consoleIoHandlerAddress = sshAddress
consoleIoHandlerUserName = sshUser
consoleIoHandlerPassword = sshPassword
consoleIoHandlerBaudrate = 115200
consoleIoHandlerPort = 5005
consoleIoHandlerPath = "/dev/ttyACM0"
consoleIoHandlerVPortName = consoleVTTY
consoleIoHandlerVerbose = True

uart4IoHandlerAddress = sshAddress
uart4IoHandlerUserName = sshUser
uart4IoHandlerPassword = sshPassword
uart4IoHandlerBaudrate = 38400
uart4IoHandlerPort = 5006
uart4IoHandlerPath = "/dev/serial0"
uart4IoHandlerVPortName = uart4VTTY
uart4IoHandlerVerbose = True

gdbServer = {   "address" : gdbServerAddress,
                "username" : gdbServerUserName,
                "password" : gdbServerPassword,
                "path" : gdbServerPath,
                "args" : gdbServerArgs,
                "verbose" : gdbServerVerbose}

gdb = { "address" : gdbAddress,
        "path" : gdbPath,
        "verbose" : gdbVerbose}

consoleIoHandler = {   "uartId" : consoleIoHandlerID,
                    "address" : consoleIoHandlerAddress,
                    "username" : consoleIoHandlerUserName,
                    "password" : consoleIoHandlerPassword,
                    "baudrate" : consoleIoHandlerBaudrate,
                    "port" : consoleIoHandlerPort,
                    "path" : consoleIoHandlerPath,
                    "vPortName" : None,
                    "verbose" : consoleIoHandlerVerbose}

uart4IoHandler = {
                    "address" : uart4IoHandlerAddress,
                    "username" : uart4IoHandlerUserName,
                    "password" : uart4IoHandlerPassword,
                    "baudrate" : uart4IoHandlerBaudrate,
                    "port" : uart4IoHandlerPort,
                    "path" : uart4IoHandlerPath,
                    "vPortName" : uart4IoHandlerVPortName,
                    "verbose" : uart4IoHandlerVerbose
}

gdbRunner = gdb_runner.gdb_runner(gdbServer, gdb, consoleIoHandler, uart4IoHandler)
gdbRunner.startOnGdb(binary)
gdbRunner.waitToFinishOnGdb()
