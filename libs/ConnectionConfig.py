# This file is part of the Test Environment build system.
#
# @copyright 2021 N7 Space Sp. z o.o.
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

from __future__ import annotations

from typing import NamedTuple, Optional


class ConnectionConfig(NamedTuple):
    """
    Tuple representing SSH connection configuration.
    """

    address: str
    username: str
    password: str

    def host(self) -> str:
        return self.address.split(":")[0]

    def port(self, fallback: int = None) -> int:
        pair = self.address.split(":")
        return int(pair[1]) if len(pair) > 1 else fallback

    @staticmethod
    def fromConfig(config: dict) -> Optional[ConnectionConfig]:
        if "address" not in config:
            return None
        return ConnectionConfig(**{k: config[k] for k in ConnectionConfig._fields})
