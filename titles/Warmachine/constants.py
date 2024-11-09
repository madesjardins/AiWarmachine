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
"""Warmachine game title constants."""

import os

VERSION = "v0.0.1"  # major.minor.build

NARRATOR_INTRODUCTION = "Welcome to Warmachine. Please, customize the options and press the start button."

DATA_DIR_PATH = f"{os.path.dirname(__file__)}/data"

MODEL_INFO_DATABASE_DIR_PATH = f"{DATA_DIR_PATH}/models"
