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

import os
import shutil
import subprocess
import time

import paramiko


class RemoteAppInvoker:
    """
    Utility class for executing custom applications either locally or via SSH,
    depending on configuration.
    """

    def __init__(
        self,
        path,
        args="",
        connectionConfig=None,
        initDelay=None,
    ):

        super().__init__()

        self.path = path
        self.args = args
        self.connectionConfig = connectionConfig

        self.initDelay = initDelay
        self.running = False
        self.handle = None
        self.pid = None

        self.sshOpened = False

    def __launchLocally(self):
        self.output = ""
        binPath = (
            os.path.realpath(self.path)
            if os.path.isfile(os.path.realpath(self.path))
            else shutil.which(self.path)
        )
        cmd = [binPath] + (
            [arg.strip() for arg in self.args.split()] if self.args is not None else []
        )
        print("Executing locally:", " ".join(cmd))
        self.handle = subprocess.Popen(
            cmd,
            shell=False,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def __launchRemotely(self):
        self.openSsh()
        command = "echo $$; exec " + self.path + " " + self.args
        print("Executing remotely:", command)
        (
            self.handle.stdin,
            self.handle.stdout,
            self.handle.stderr,
        ) = self.handle.exec_command(command, get_pty=True)
        self.pid = int(self.handle.stdout.readline())

    def open(self):
        if self.running:
            return

        if self.connectionConfig is not None:
            self.__launchRemotely()
        else:
            self.__launchLocally()

        if self.initDelay is not None:
            time.sleep(self.initDelay)

        self.running = True

    def __shutdownLocally(self):
        self.handle.terminate()

    def __shutdownRemotely(self):
        self.handle.exec_command(
            "kill " + str(self.pid),
        )
        self.handle.close()
        self.sshOpened = False

    def close(self):
        if self.connectionConfig is not None:
            self.__shutdownRemotely()
        else:
            self.__shutdownLocally()

        self.handle = None
        self.reader = None
        self.running = False

    def openSsh(self):
        if self.sshOpened:
            return

        try:
            self.handle = paramiko.SSHClient()
            self.handle.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.handle.connect(
                self.connectionConfig.host(),
                self.connectionConfig.port(22),
                self.connectionConfig.username,
                self.connectionConfig.password,
            )
        except Exception:
            if self.handle is not None and self.handle._transport is not None:
                self.handle.close()
            self.handle = None
            raise

        self.sshOpened = True
