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
"""Viewport label widget."""

from PyQt6 import QtCore, QtWidgets


class ViewportLabel(QtWidgets.QLabel):
    """QLabel with mouse event."""

    mouse_press_event = QtCore.pyqtSignal(float, float)
    mouse_drag_event = QtCore.pyqtSignal(float, float)
    key_press_event = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        """Initialize.

        :param parent: Parent Widget. (None)
        :type parent: :class:`QWidget`
        """
        super().__init__(parent=parent)
        self.pix_size = QtCore.QSize(1, 1)
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignLeft)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.is_pressed = False

    def get_normalized_pos(self, pos):
        """Get the normalized position of the mouse event.

        :param pos: Position in pixels.
        :type pos: :class:`QSize`

        :return: Normalized x and y values [0, 1[.
        :rtype: tuple[float, float]
        """
        width = self.pix_size.width()
        height = self.pix_size.height()
        return (
            min(max(0, pos.x() / width), (width - 1) / width),
            min(max(0, pos.y() / height), (height - 1) / height)
        )

    def get_safe_pos(self, pos):
        """Get the position of the mouse event within the limit of the resolution.

        :param pos: Position in pixels.
        :type pos: :class:`QSize`

        :return: X and y values in pixels.
        :rtype: tuple[int, int]
        """
        width = self.pix_size.width()
        height = self.pix_size.height()
        return (
            min(max(0, pos.x()), (width - 1)),
            min(max(0, pos.y()), (height - 1))
        )

    def mousePressEvent(self, event):
        """Mouse press event."""
        self.is_pressed = True
        rel_pos_x, rel_pos_y = self.get_normalized_pos(event.pos())
        self.mouse_press_event.emit(rel_pos_x, rel_pos_y)

    def mouseMoveEvent(self, event):
        """Mouse press event."""
        if self.is_pressed:
            rel_pos_x, rel_pos_y = self.get_normalized_pos(event.pos())
            self.mouse_drag_event.emit(rel_pos_x, rel_pos_y)

    def mouseReleaseEvent(self, event):
        """Mouse release event."""
        self.is_pressed = False

    def keyPressEvent(self, event):
        """A key was pressed."""
        self.key_press_event.emit(event.text())

    def setPixmap(self, image, fixed_size=True):
        """Set Pixmap"""
        if self.pix_size != image.size():
            self.pix_size = image.size()
            if fixed_size:
                self.setFixedSize(self.pix_size)

        super().setPixmap(image)
        self.repaint()
