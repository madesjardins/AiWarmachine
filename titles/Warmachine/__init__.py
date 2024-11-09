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
"""Warmachine title."""

from importlib import reload

from PyQt6 import QtCore

from . import core, dialog
reload(core)
reload(dialog)


class Title(QtCore.QObject):
    """Small class containing title core and dialog."""

    def __init__(self, main_core, main_window):
        """Initialize."""
        super().__init__()
        self.title_core = core.TitleCore(main_core)
        self.title_dialog = dialog.TitleDialog(self.title_core, main_window)
        self.title_dialog.closing.connect(main_window.title_closing)


def launch(main_core, main_window):
    """Launch this title.

    :param main_core: The title core.
    :type main_core: :class:`MainCore`

    :param main_window: The main window.
    :type main_window: :class:`MainWindow`

    :return: Title.
    :rtype: :class:`Title`
    """
    return Title(main_core, main_window)
