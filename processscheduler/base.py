"""This module contains fundamental classes/functions that are used everywhere in the project."""

# Copyright (c) 2020-2021 Thomas Paviot (tpaviot@gmail.com)
#
# This file is part of ProcessScheduler.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.

import os
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, PositiveInt, Field, Extra, ConfigDict

import z3


class BaseModelWithJson(BaseModel):
    """The base object for most ProcessScheduler classes"""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    name: str = Field(default=None)
    type: str = Field(default=None)

    def __init__(self, **data) -> None:
        """The base name for all ProcessScheduler objects.

        Provides an assertions list, a uniqueid.

        Args:
            name: the object name. It must be unique
        """
        # check name type
        super().__init__(**data)

        self._uid = uuid4().int

        if self.name is None:
            self.name = f"{self.__class__.__name__}_{str(self._uid)[:8]}"

        self.type = f"{self.__class__.__name__}"

    def __hash__(self) -> int:
        return self._uid

    def __eq__(self, other) -> bool:
        return self._uid == other._uid

    # def __repr__(self) -> str:
    #     """Print the object name, its uid and the assertions."""
    #     str_to_return = (
    #         f"{self.name}({type(self)})\n{len(self._z3_assertions)} assertion(s):\n"
    #     )
    #     assertions_str = "".join(f"{assertion}" for assertion in self._z3_assertions)
    #     return str_to_return + assertions_str

    def to_json(self, compact=False):
        """return a json string"""
        return self.model_dump_json(indent=None if compact else 4)

    def to_json_file(self, filename, compact=False):
        with open(filename, "w") as f:
            f.write(self.to_json(compact))
        return os.path.isfile(filename)  # success


#
# NamedUIDObject, name and uid for hashing
#
class NamedUIDObject(BaseModelWithJson):
    """The base object for most ProcessScheduler classes"""

    def __init__(self, **data) -> None:
        super().__init__(**data)

        # SMT assertions
        # start and end integer values must be positive
        self._z3_assertions = []  # type: List[z3.BoolRef]
        self._z3_assertion_hashes = []

    def __repr__(self) -> str:
        """Print the object name, its uid and the assertions."""
        str_to_return = (
            f"{self.name}({type(self)})\n{len(self._z3_assertions)} assertion(s):\n"
        )
        assertions_str = "".join(f"{assertion}" for assertion in self._z3_assertions)
        return str_to_return + assertions_str

    def append_z3_list_of_assertions(
        self, list_of_z3_assertions: List[z3.BoolRef]
    ) -> None:
        for z3_asst in list_of_z3_assertions:
            self.append_z3_assertion(z3_asst)

    def append_z3_assertion(self, z3_assertion: z3.BoolRef) -> bool:
        """
        Add a z3 assertion to the list of assertions to be satisfied.

        Args:
            z3_assertion: the z3 assertion
        """
        # check if the assertion is in the list
        # workaround to avoid heavy hash computations
        assertion_hash = hash(z3_assertion)
        if assertion_hash in self._z3_assertion_hashes:
            raise AssertionError(f"assertion {z3_assertion} already added.")
        self._z3_assertions.append(z3_assertion)
        self._z3_assertion_hashes.append(assertion_hash)
        return True

    def get_z3_assertions(self) -> List[z3.BoolRef]:
        """Return the assertions list"""
        return self._z3_assertions


# Define a global problem
# None by default
# the scheduling problem will set this variable
active_problem = None


def clear_active_problem() -> None:
    """Clear current context"""
    if active_problem is not None:
        active_problem.clear()
