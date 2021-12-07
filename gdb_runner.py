# This file is part of the Test Environment build system.
#
# @copyright 2020-2021 N7 Space Sp. z o.o.
#
# Test Environment was developed under a programme of,
# and funded by, the European Space Agency (the "ESA").
#
#
# Licensed under the ESA Public License (ESA-PL) Permissive,
# Version 2.3 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://essr.esa.int/license/list
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import binascii
import atexit
import time
import timeout_decorator

from libs.GdbInterface import GdbInterface
from libs.GdbServerInvoker import GdbServerInvoker
from libs.ConnectionConfig import ConnectionConfig

class gdb_runner:
    __gdbSrv = None
    __gdb = None
    __ioConsole = None
    __ioUart4 = None

    __gdbSrvConfig = dict()
    __gdbConfig = dict()
    __consoleConfig = dict()
    __uart4Config = dict()

    def __init__(self, gdbSrvConfig, gdbConfig, consoleConfig, uart4Config):
        self.__gdbSrvConfig = gdbSrvConfig
        self.__gdbConfig = gdbConfig
        self.__consoleConfig = consoleConfig
        self.__uart4Config = uart4Config

    def __log(msg, *args, **kwargs):
        print("GDB-RUNNER:", msg, *args, **kwargs)


    def __invokeGdbServer(self):
        self.__log("Starting GDB server...")
        srv = GdbServerInvoker(
            self.__gdbSrvConfig["path"],
            self.__gdbSrvConfig["args"],
            ConnectionConfig.fromConfig(self.__gdbSrvConfig),
            verbosity=True,
        )
        srv.open()
        time.sleep(1)
        return srv


    def __invokeGdb(self):
        self.__log("Staring GDB...")
        gdb = GdbInterface(
            self.__gdbConfig["address"],
            self.__gdbConfig["path"],
            verbose=self.__gdbConfig["verbose"],
        )
        gdb.launch()
        return gdb


    def __openIoHandler(self, config):
        self.__log("Starting IO Handler...")

        from libs.UartIoHandler import UartIoHandler
        handler = UartIoHandler(
                config["address"],
                config["username"],
                config["password"],
                config["path"],
                config["baudrate"],
                config["port"],
                config["vPortName"],
                debug=config["verbose"],
            )
        handler.open()
        return handler


    def __dumpLogLambda(self, io, logPath):
        with open(logPath, "wb") as logFile:
            while True:
                data = io.receive(io.getOptimalReadSize())
                if len(data) == 0:
                    return
                logFile.write(data)


    def __dumpLog(self, io, logPath, timeout):
        @timeout_decorator.timeout(timeout)
        def dumpLogTimeout(io, logPath):
            self.__dumpLogLambda(io, logPath)

        if timeout != 0:
            dumpLogTimeout(io, logPath)

        else:
            self.__dumpLogLambda(io, logPath)


    def __cleanup(self):#**ignored):
        if self.__ioConsole is not None:
            self.__log("Cleaning IO Handler...")
            self.__ioConsole.close()
            self.__ioConsole = None
        if self.__ioUart4 is not None:
            self.__log("Cleaning IO Handler...")
            self.__ioUart4.close()
            self.__ioUart4 = None
        if self.__gdb is not None:
            self.__log("Cleaning GDB...")
            self.__gdb.shutdown()
            self.__gdb = None
        if self.__gdbSrv is not None:
            self.__log("Cleaning GDB Server...")
            self.__gdbSrv.close()
            self.__gdbSrv = None


    def initTestEnv(self):
        if self.__gdbSrv is None:
            self.__gdbSrv = self.__invokeGdbServer()

        if self.__gdb is None:
            self.__gdb = self.__invokeGdb()

        if self.__ioConsole is None:
            self.__ioConsole = self.__openIoHandler(self.__consoleConfig)
        else:
            self.__ioConsole.reset()

        if self.__ioUart4 is None:
            self.__ioUart4 = self.__openIoHandler(self.__uart4Config)
        else:
            self.__ioUart4.reset()

        atexit.register(self.__cleanup)


    def startOnGdb(self, binaryPath):
        self.initTestEnv()

        self.__gdb.reset()
        self.__gdb.load(binaryPath)
        self.__gdb.execCmd("set $pc = &Reset_Handler")
        self.__gdb.execCmd("set $sp = &_estack")
        self.__log("Starting execution...")
        self.__gdb.start()
        self.__log("Execution started.")

    def waitToFinishOnGdb(self):
        
        if self.__gdb.isRunning():
            try:
                self.__log("Waiting for GDB to finish...")
                if not self.__gdb.waitForFinish(timeout=int(100)):
                    self.__gdb.stop()
            except Exception as e:
                self.__log(e)
                self.__gdb.stop()

        self.__log("Execution finished.")
        self.__gdb.execCmd("bt", pollUntilDone=True)
        self.__gdb.execCmd("info reg", pollUntilDone=True)
        self.__log("Downloading logs...")
        self.__dumpLog(self.__ioConsole, "vConsoleLog.txt", 0)
        self.__dumpLog(self.__ioUart4, "vUart4log.txt", 0)
        self.__log("Log dumped.")


    def __readMemoryFromGdb(self, env, address, size=4):
        self.initTestEnv(env)

        self.__log(f"Reading from 0x{address:08x}")
        value = self.__gdb.rmem(address, size)
        self.__log(f"0x{address:08x}: {value.hex()}")
        return value

    def __convertCoverageLog(logFileName):
        fileName = None
        with open(logFileName) as log:
            for line in log.readlines():
                if line.startswith(">>>"):
                    fileName = line[3:-1]
                elif fileName is not None:
                    with open(fileName, "wb") as outFile:
                        outFile.write(binascii.a2b_hex(line.strip()))
                    fileName = None


    def __removeCoverageFromLog(source, target):
        logLines = []
        with open(source) as log:
            for line in log:
                logLines.append(line)
                if line == ">> COVERAGE RESULT - BEGIN <<\n":
                    logLines = logLines[:-2]  # begin line and \n before it
                    break
        with open(target, "w") as log:
            log.writelines(logLines)
