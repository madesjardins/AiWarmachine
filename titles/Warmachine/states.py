#
# This file is part of the AiWarmachine distribution (https://github.com/madesjardins/AiWarmachine).
# Copyright (c) 2023-2024 Marc-Antoine Desjardins.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
"""Module for all states class."""

from enum import Enum


class TitleState(Enum):
    """Title states corresponds to states that are always present in this title."""
    MENU = 0
    ARMY = 1
    TERRAIN = 2
    DEPLOYMENT = 3
    MATCH = 4
    END = 5


class TurnState(Enum):
    """The 3 phases of a turn during a match."""
    MAINTENANCE = 0
    CONTROL = 1
    ACTIVATION = 2


class ActivationState(Enum):
    """Activation states."""
    MOVEMENT = 0
    COMBAT = 1
