#
# This file is part of the AiWarmachine distribution (https://github.com/madesjardins/AiWarmachine).
# Copyright (c) 2023 Marc-Antoine Desjardins.
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
"""Tick generator."""

import time

from PyQt6 import QtCore

from . import constants


class TickGenerator(QtCore.QThread):
    """A simple threaded object to generate ticks at an approximative rate."""

    # tick signal sends time since start in seconds.
    tick = QtCore.pyqtSignal(float, float)

    def __init__(self, tps=constants.DEFAULT_FPS):
        """Initialize.

        :param tps: Ticks per second. (constants.DEFAULT_FPS)
        :type tps: float
        """
        super().__init__()
        self.time_interval = 1.0 / tps
        self.is_running = False
        self.running_time = 0.0

    def run(self):
        """Generate ticks."""
        self.is_running = True
        self.running_time = 0.0
        start_time = time.time()
        while self.is_running:
            self.tick.emit(self.running_time, self.time_interval)
            time.sleep(self.time_interval)
            self.running_time = time.time() - start_time
            QtCore.QCoreApplication.processEvents()

    def stop(self):
        self.is_running = False
