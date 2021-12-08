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

import select
import socket
import time
import os

import paramiko
import scp
from serial import PARITY_EVEN, PARITY_NONE, PARITY_ODD

from .IoHandler import IoHandler


class UartIoHandler(IoHandler):
    """
    Class responsible for gathering the output of the application executed on HWTB,
    when the output is transimtted over UART (forwarded via `socat`).
    """

    OPTIMAL_READ_SIZE = 4096

    def getOptimalReadSize(self):
        return self.OPTIMAL_READ_SIZE

    def __init__(
        self,
        address,
        username,
        password,
        uartDevice,
        uartBaud,
        port,
        vPortName=None,
        parity=PARITY_NONE,
        debug=False,
    ):
        self.address = address
        self.port = int(port)

        if vPortName == '':
            self.redirectTraficToPty = False
        else :
            self.vPortName = vPortName
            self.redirectTraficToPty = True

        self.username = username
        self.password = password

        self.uartDevice = uartDevice
        self.uartBaud = uartBaud

        self.sshUart = None
        self.uartSocket = None
        self.opened = False
        self.handle = None
        self.parity = parity

        self.debug = debug

    def _openUartSocket(self):
        try:
            self.uartSocket = socket.socket()
            self.uartSocket.connect((self.address, self.port))
        except socket.error:
            self.sshUart.uartSession.send(chr(3))
            time.sleep(0.5)
            self.sshUart.close()
            raise

    def _linkSocketWithVirtualTty(self):
        try:
            socatLinkString = (
                "socat pty,link="
                + self.vPortName
                +",raw,echo=0 tcp:"
                + str(self.address)
                + ":"
                + str(self.port)
                + " &"
            )
            os.system(socatLinkString)
        except os.error:
            raise RuntimeError("Couldn't link socket with virtual tty.")

    def _spawnRemoteSocat(self):
        debugFlag = "-x" if self.debug else ""
        socatExecString = (
            "socat "
            + debugFlag
            + " tcp-l:"
            + str(self.port)
            + ",reuseaddr,fork "
            + self.uartDevice
            + ",raw,echo=0,b"
            + str(self.uartBaud)
            + " &> socat_"
            + self.uartDevice.replace("/", "")
            + "_gdb.log"
        )
        sttyArgs = str(self.uartBaud) + " cs8 -cstopb -crtscts "
        if self.parity == PARITY_EVEN:
            sttyArgs += "parenb -parodd"
        elif self.parity == PARITY_ODD:
            sttyArgs += "parenb parodd"
        elif self.parity == PARITY_NONE:
            sttyArgs += "-parenb"
        else:
            raise RuntimeError("Invalid parity settings supplied.")

        sshUart = self.sshUart
        try:
            transport = sshUart.get_transport()
            uartSession = transport.open_session()
            uartSession.get_pty()
            uartSession.invoke_shell()
            time.sleep(2)
            uartSession.send("stty -F " + self.uartDevice + " " + sttyArgs + "\n")
            time.sleep(1)
            uartSession.send(socatExecString + "\n")
            time.sleep(1)
            sshUart.uartSession = uartSession
        except paramiko.SSHException:
            sshUart.close()
            raise

    def __checkIfLaunched(self):
        psout = (
            self.sshUart.exec_command("ps | grep socat")[1]
            .read()
            .decode("utf-8")
            .splitlines()
        )

        for line in psout:
            if "socat" in line:
                return True
        return False

    def open(self):
        super().open()
        if self.opened:
            raise RuntimeError(
                "UartIoHandler has to be closed before opening it again!"
            )

        try:
            self.sshUart = paramiko.SSHClient()
            self.sshUart.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.sshUart.connect(self.address, 22, self.username, self.password)

            if self.__checkIfLaunched():
                raise RuntimeError("UartIoHandler is already running elsewhere.")
            self._spawnRemoteSocat()
            
            if self.redirectTraficToPty:
                self._linkSocketWithVirtualTty()
            else:
                self._openUartSocket()
                self.handle = self.uartSocket.fileno()
                self.opened = True

        except Exception:
            if self.sshUart is not None and self.sshUart._transport is not None:
                self.checkAndForceClose()
                self.sshUart.close()
            self.sshUart = None
            raise

    def checkAndForceClose(self):
        psout = (
            self.sshUart.exec_command("ps | grep socat")[1]
            .read()
            .decode("utf-8")
            .splitlines()
        )

        for line in psout:
            if "socat" in line:
                self.sshUart.exec_command("kill " + str(line.split()[0]))
                break

    def close(self):
        if not self.opened:
            return

        self.opened = False
        self.handle = None

        self.uartSocket.shutdown(socket.SHUT_RDWR)
        self.uartSocket.close()
        self.uartSocket = None

        if self.debug:
            scpClient = scp.SCPClient(self.sshUart.get_transport())
            scpClient.get("socat_" + self.uartDevice.replace("/", "") + "_gdb.log")
            scpClient.close()

        self.checkAndForceClose()
        self.sshUart.close()
        self.sshUart = None

        super().close()

    def send(self, data):
        if self.uartSocket is None:
            raise RuntimeError("The UART handler has not been open()'d!")

        self.uartSocket.send(data)

    def receive(self, maxlen=1, timeout=1):
        if self.uartSocket is None:
            raise RuntimeError("The UART handler has not been open()'d!")

        data = b""
        if timeout > 0:
            try:
                readable, _, _ = select.select([self.uartSocket], [], [], timeout)
                if readable:
                    data = self.uartSocket.recv(maxlen)
            except OSError:
                pass
        else:
            while True:
                try:
                    readable, _, _ = select.select([self.uartSocket], [], [], 1)
                    if readable:
                        data = self.uartSocket.recv(maxlen)
                        break
                except OSError:
                    break
        return data

    def reset(self):
        while len(self.receive(8 * 1024)) > 0:
            pass  # read all cached incoming bytes
        super().reset()
