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

from __future__ import print_function
import time
from pygdbmi.gdbcontroller import GdbController
from pygdbmi.constants import GdbTimeoutError

import timeout_decorator


class GdbInvalidCommandError(ValueError):
    """
    Exception indicating invalid GDB command.
    """

    pass


class GdbRuntimeError(RuntimeError):
    """
    Exception indicating GDB runtime error.
    """

    pass


class GdbCommunicationError(EnvironmentError):
    """
    Exception indicating error while trying to communicate with GDB server.
    """

    pass


class GdbInterface:
    """
    Class representing connection to the GDB server.
    """

    def __init__(self, address, path="gdb", verbose=False):
        self.address = address
        self.verbose = verbose
        self.path = path

        self.gdbmi = None
        self.running = False
        self.launched = False

    def printVerbose(self, *args, **kwargs):
        if self.verbose:
            msg = args[0].replace("\\n", "\n")
            msg = msg.replace("\\t", "\t")
            print(msg, *args[1:], **kwargs)

    def printFormatedResponse(self, response):
        console_msgs = [
            entry["payload"] for entry in response if entry["type"] == "console"
        ]
        for msg in console_msgs:
            self.printVerbose(msg, end="")
        errors = [
            entry["payload"]["msg"] for entry in response if entry["message"] == "error"
        ]
        if errors:
            raise GdbRuntimeError(errors[0])

    def execCmd(self, command, pollUntilDone=False):
        response = self.execCmdAsync(command)
        if not [x for x in response if x["message"] == "done"]:
            if pollUntilDone:
                response += self._pollUntilDone()
            else:
                self.waitForFinish()
        return response

    def execCmdAsync(self, command):
        self.printVerbose(" " + command)

        try:
            response = self.gdbmi.write(command)
        except TypeError:
            raise GdbInvalidCommandError(
                "Invalid command supplied to execCmd: " + str(command)
            )

        self.printFormatedResponse(response)
        return response

    def monitor(self, command, pollUntilDone=False):
        return self.execCmd(command, pollUntilDone)

    def launch(self):
        self.gdbmi = GdbController([self.path, "--interpreter=mi3"])
        time.sleep(1)

        self.monitor("target extended-remote " + self.address)
        # self.monitor("set download-write-size 4096")
        self.monitor("set remote memory-write-packet-size 1024")
        self.monitor("set remote memory-write-packet-size fixed")
        self.monitor("set remote memory-read-packet-size 4096")
        self.monitor("set remote memory-read-packet-size fixed")
        self.monitor("set remotetimeout 30")
        self.launched = True

    def load(self, path):
        self.monitor("file " + path)
        self.monitor("load")

    def reset(self):
        self.monitor("monitor reset halt")

    def start(self):
        self.running = True
        response = self.execCmdAsync("continue")
        if self._checkIfExecutionStopped(response):
            self.running = False

    def _checkIfExecutionStopped(self, response):
        return [
            x for x in response if x["message"] == "done" or x["message"] == "stopped"
        ]

    def _pollUntilDone(self):
        output = []
        while True:
            try:
                response = self.gdbmi.get_gdb_response(timeout_sec=1000)
            except timeout_decorator.TimeoutError as error:
                raise GdbTimeoutError(error)
            self.printFormatedResponse(response)
            output += response
            if self._checkIfExecutionStopped(response):
                break
        return output

    def waitForFinish(self, timeout=0):
        def _waitForDoneLambda():
            self._pollUntilDone()
            self.running = False

        @timeout_decorator.timeout(timeout)
        def _waitForDone():
            _waitForDoneLambda()

        if timeout == 0:
            _waitForDoneLambda()
            return True

        try:
            _waitForDone()
            return True
        except GdbTimeoutError:
            return False

    def terminate(self):
        if self.running:
            self.gdbmi.interrupt_gdb()
            self.gdbmi.exit
            self.running = False

    def stop(self):
        if self.running:
            self.gdbmi.interrupt_gdb()

            self.waitForFinish()
        self.running = False

    def shutdown(self):
        self.stop()

        if self.launched:
            self.launched = False
            self.gdbmi.exit()

        self.running = False
        self.gdbmi = None

    def rmem(self, address, count=4):
        response = self.monitor(
            "x/" + str(count) + "ub " + hex(address), pollUntilDone=True
        )
        outbytes = bytearray()
        for entry in [
            entry["payload"] for entry in response if entry["type"] == "console"
        ]:
            for byte in entry.split("\\t")[1:]:
                outbytes.append(int(byte.split("\\n")[0]))

        return outbytes

    def isRunning(self):
        return self.running
