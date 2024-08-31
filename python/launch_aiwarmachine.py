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
"""Application launcher."""

import os
import sys

from PyQt6 import QtWidgets, QtGui, QtCore

from AiWarmachine import main_core, main_window, constants, voice_narration

# Verify installation
if not os.path.exists(constants.PIPER_EXECUTABLE):
    raise RuntimeError(f'Unable to find "{constants.PIPER_EXECUTABLE}".')

if not voice_narration.get_available_voices():
    raise RuntimeError(
        f'Unable to find voices for piper.exe in "{constants.PIPER_VOICES_DIRPATH}".\n'
        'Make sure X.onnx files have corresponding X.onnx.json files.'
    )

if not os.path.exists(constants.TEMP_DIRPATH):
    os.makedirs(constants.TEMP_DIRPATH)

app = QtWidgets.QApplication(sys.argv)

# Dark theme Palette
app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
palette = QtGui.QPalette()
silver = QtGui.QColor(192, 192, 192)
dark = QtGui.QColor(25, 25, 25)
palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(64, 64, 64))
palette.setColor(QtGui.QPalette.ColorRole.WindowText, silver)
palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(48, 48, 48))
palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(64, 64, 64))
palette.setColor(QtGui.QPalette.ColorRole.ToolTipBase, dark)
palette.setColor(QtGui.QPalette.ColorRole.ToolTipText, silver)
palette.setColor(QtGui.QPalette.ColorRole.Text, silver)
palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(64, 64, 64))
palette.setColor(QtGui.QPalette.ColorRole.ButtonText, silver)
palette.setColor(QtGui.QPalette.ColorRole.BrightText, QtCore.Qt.GlobalColor.red)
palette.setColor(QtGui.QPalette.ColorRole.Link, QtGui.QColor(42, 130, 218))
palette.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor(42, 130, 218))
palette.setColor(QtGui.QPalette.ColorRole.HighlightedText, dark)
app.setPalette(palette)

app.setStyleSheet(
    "QPushButton:disabled {background-color: rgb(86, 64, 64);}\n"
    "QComboBox:disabled {background-color: rgb(86, 64, 64);}\n"
    "QSlider:disabled {background-color: rgb(86, 64, 64);}\n"
    "QLineEdit:disabled {color: rgb(86, 112, 164);}\n"
)

main_core = main_core.MainCore()
cal_win = main_window.MainWindow(core=main_core, parent=None)
app.exec()
