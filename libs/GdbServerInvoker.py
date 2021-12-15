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

import sys
import threading

from .RemoteAppInvoker import RemoteAppInvoker


class GdbServerInvoker(RemoteAppInvoker):
    """
    Class responsible for invoking GDB server.
    It can invoke it locally or remotely via SSH.
    """

    def __init__(
        self,
        path,
        args="",
        config=None,
        initDelay=None,
        verbosity=False,
    ):

        super().__init__(path, args, config, initDelay)
        if not verbosity:
            self.args += " -silent"

        self.reader = None
        self.verbose = verbosity
        self.output = ""

    def open(self):
        super().open()

        self.reader = threading.Thread(
            target=self.__stdoutRead, kwargs={"stdout": self.handle.stdout}
        )
        self.reader.daemon = True
        self.reader.kill = threading.Event()
        self.reader.start()

    def close(self):
        self.reader.kill.set()
        self.reader.join(timeout=1)

        super().close()
        self.reader = None

    def __stdoutRead(self, stdout):
        if self.handle is None:
            return

        while not self.reader.kill.is_set():
            out = stdout.read(1)
            if isinstance(out, (bytes, bytearray)):
                out = out.decode("utf-8")
            if out != "":
                self.output += out
                if self.verbose:
                    sys.stdout.write(out)
                    sys.stdout.flush()
            else:
                break
