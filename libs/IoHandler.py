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

from abc import ABC, abstractmethod


class IoHandler(ABC):
    """
    Interface for handling output of the application executed on HWTB.
    """

    @abstractmethod
    def getOptimalReadSize(self):
        pass

    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def receive(self, maxlen, timeout):
        pass

    @abstractmethod
    def reset(self):
        pass
