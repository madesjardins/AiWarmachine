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
"""Projector dialog."""

from functools import partial
import copy

from PyQt6 import QtCore, QtWidgets, QtGui
import numpy as np
import cv2 as cv

from . import viewport_label, constants, common


MOVE_KEY_POINTS_DICT = {
    "a": QtCore.QPoint(-1, 0),
    "s": QtCore.QPoint(0, -1),
    "d": QtCore.QPoint(1, 0),
    "w": QtCore.QPoint(0, 1),
}


class ProjectorDialog(QtWidgets.QDialog):
    """Projector dialog to draw information on board."""

    corner_changed = QtCore.pyqtSignal(int, QtCore.QPoint)

    def __init__(self, parent=None):
        """Initialize.

        :param parent: The parent widget. (None)
        :type parent: :class:`QWidget`
        """
        super().__init__(parent=parent, flags=QtCore.Qt.WindowType.WindowTitleHint | QtCore.Qt.WindowType.CustomizeWindowHint)
        self._is_fullscreen = False
        self._corner_points_list = [
            QtCore.QPoint(10, 260),
            QtCore.QPoint(10, 10),
            QtCore.QPoint(460, 10),
            QtCore.QPoint(460, 260),
        ]
        self._selected_corner_index = None
        self._selected_corner_offset = QtCore.QPoint(0, 0)
        self._corners_are_visible = False
        self._borders_in_bold = False
        self._game_to_projector_matrix = None
        self._game_overlay = None
        self._init_ui()
        self._init_connections()
        self.show()

    def _init_ui(self):
        """Initialize the UI."""
        self.setWindowTitle("Projector")
        layout = QtWidgets.QVBoxLayout()
        self.viewport_label = viewport_label.ViewportLabel(self)
        layout.addWidget(self.viewport_label)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._base_image = QtGui.QImage(
            480,
            270,
            QtGui.QImage.Format.Format_BGR888
        )
        self._base_image.fill(QtCore.Qt.GlobalColor.black)
        self.refresh_image()

    def _init_connections(self):
        """Initialize the UI."""
        self.viewport_label.key_press_event.connect(self.key_pressed)
        self.viewport_label.mouse_press_event.connect(partial(self.update_corners, True))
        self.viewport_label.mouse_drag_event.connect(partial(self.update_corners, False))

    @QtCore.pyqtSlot(str)
    def key_pressed(self, key_text):
        """A key was pressed.

        :param key_text: The text value of the key.
        :type key_text: str
        """
        if key_text == "f":
            if self._is_fullscreen:
                geometry = self.geometry()
                self._base_image = self._base_image.scaled(
                    480,
                    270,
                    aspectRatioMode=QtCore.Qt.AspectRatioMode.IgnoreAspectRatio
                )
                self.refresh_image()
                self.setGeometry(geometry.x() + 256, geometry.y() + 256, 480, 270)
            else:
                self.showFullScreen()
                size = self.geometry().size()
                self._base_image = self._base_image.scaled(
                    size.width(),
                    size.height(),
                    aspectRatioMode=QtCore.Qt.AspectRatioMode.IgnoreAspectRatio
                )
                self.refresh_image()

            self._is_fullscreen = not self._is_fullscreen
            self.resize(self.viewport_label.sizeHint())

        elif key_text == "c":
            self._corners_are_visible = not self._corners_are_visible
            self.update_corner_overlay()

        elif key_text == "b":
            self._borders_in_bold = not self._borders_in_bold
            self.update_corner_overlay()

        elif key_text in MOVE_KEY_POINTS_DICT and self._selected_corner_index is not None:
            width = self._base_image.width()
            height = self._base_image.height()

            self._corner_points_list[self._selected_corner_index].setX(
                min(max(0, self._corner_points_list[self._selected_corner_index].x() + MOVE_KEY_POINTS_DICT[key_text].x()), width - 1)
            )
            self._corner_points_list[self._selected_corner_index].setY(
                min(max(0, self._corner_points_list[self._selected_corner_index].y() + MOVE_KEY_POINTS_DICT[key_text].y()), height - 1)
            )
            self.update_corner_overlay()

    @QtCore.pyqtSlot(bool, float, float)
    def update_corners(self, is_pressed, norm_pos_x, norm_pos_y):
        """"""
        width = self._base_image.width()
        height = self._base_image.height()

        if is_pressed:
            pos_mouse = QtCore.QPoint(int(norm_pos_x * width), int(norm_pos_y * height))

            self._selected_corner_index = None
            closest_corner_index = None
            closest_distance = None

            for corner_index in constants.TABLE_CORNERS_DRAWING_ORDER:
                test_pos = self._corner_points_list[corner_index] - pos_mouse
                test_distance = test_pos.manhattanLength()
                if (
                    test_distance < constants.MAXIMUM_CLOSEST_TABLE_CORNER_DISTANCE and
                    (
                        closest_distance is None or
                        test_distance < closest_distance
                    )
                ):
                    closest_corner_index = corner_index
                    closest_distance = test_distance

            if closest_corner_index is not None:
                self._selected_corner_index = closest_corner_index
                self._selected_corner_offset = self._corner_points_list[closest_corner_index] - pos_mouse

        elif self._selected_corner_index is not None:
            self._corner_points_list[self._selected_corner_index].setX(
                min(max(0, int(norm_pos_x * width) + self._selected_corner_offset.x()), width - 1)
            )
            self._corner_points_list[self._selected_corner_index].setY(
                min(max(0, int(norm_pos_y * height) + self._selected_corner_offset.y()), height - 1)
            )
            self.update_corner_overlay()

    def calculate_game_to_projector_matrix(self, width, height):
        """"""
        projector_points = np.float32(
            [
                [self._corner_points_list[constants.TABLE_CORNERS_INDEX_BL].x(), self._corner_points_list[constants.TABLE_CORNERS_INDEX_BL].y()],
                [self._corner_points_list[constants.TABLE_CORNERS_INDEX_TL].x(), self._corner_points_list[constants.TABLE_CORNERS_INDEX_TL].y()],
                [self._corner_points_list[constants.TABLE_CORNERS_INDEX_TR].x(), self._corner_points_list[constants.TABLE_CORNERS_INDEX_TR].y()],
                [self._corner_points_list[constants.TABLE_CORNERS_INDEX_BR].x(), self._corner_points_list[constants.TABLE_CORNERS_INDEX_BR].y()],
            ]
        )

        game_points = np.float32(
            [
                [0.0, 0.0],
                [0.0, height],
                [width, height],
                [width, 0.0]
            ]
        )

        self._game_to_projector_matrix = cv.getPerspectiveTransform(game_points, projector_points)

    @QtCore.pyqtSlot(dict)
    def update_game_overlay(self, game_qr_detection_data):
        """"""
        self._latest_game_qr_detection_data = copy.deepcopy(game_qr_detection_data)
        if self._base_image is not None and self._game_to_projector_matrix is not None:
            image = np.zeros(
                (
                    1280,  # Should be based on 1px = 1mm
                    720,
                    3
                ),
                dtype=np.uint8
            )
            image[:, :] = (0, 0, 0)
            for message, qr_data in game_qr_detection_data.items():
                cv.circle(image, qr_data['pos'], 18, (255, 255, 255), 3)

            warped_image = cv.warpPerspective(image, self._game_to_projector_matrix, (self._base_image.width(), self._base_image.height()))
            self._game_overlay = QtGui.QImage(
                warped_image,
                warped_image.shape[1],
                warped_image.shape[0],
                warped_image.strides[0],
                QtGui.QImage.Format.Format_BGR888
            )

        self.refresh_image()

    def update_corner_overlay(self):
        """"""
        self._base_image.fill(QtCore.Qt.GlobalColor.black)
        if self._corners_are_visible:
            painter = QtGui.QPainter(self._base_image)
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode.CompositionMode_Source)
            brush = QtGui.QBrush()
            painter.setBrush(brush)
            pen_size = 5 if self._borders_in_bold else 1
            pen = QtGui.QPen(QtCore.Qt.GlobalColor.white, pen_size, QtCore.Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawPolyline(self._corner_points_list + self._corner_points_list[:1])
            painter.setPen(QtGui.QPen(QtCore.Qt.GlobalColor.green, 2, QtCore.Qt.PenStyle.SolidLine))
            painter.drawEllipse(self._corner_points_list[constants.TABLE_CORNERS_INDEX_BL], 10, 10)
            painter.setPen(QtGui.QPen(QtCore.Qt.GlobalColor.blue, 2, QtCore.Qt.PenStyle.SolidLine))
            painter.drawEllipse(self._corner_points_list[constants.TABLE_CORNERS_INDEX_TL], 10, 10)
            painter.setPen(QtGui.QPen(QtCore.Qt.GlobalColor.red, 2, QtCore.Qt.PenStyle.SolidLine))
            painter.drawEllipse(self._corner_points_list[constants.TABLE_CORNERS_INDEX_TR], 10, 10)
            painter.setPen(QtGui.QPen(QtCore.Qt.GlobalColor.yellow, 2, QtCore.Qt.PenStyle.SolidLine))
            painter.drawEllipse(self._corner_points_list[constants.TABLE_CORNERS_INDEX_BR], 10, 10)
            painter.end()
        self.refresh_image()

    def refresh_image(self):
        """"""
        # Composite overlay
        if self._game_overlay is not None:
            self.set_image(
                common.composite_images(
                    self._base_image,
                    self._game_overlay,
                    image_format=QtGui.QImage.Format.Format_RGB888,
                    composite_mode=QtGui.QPainter.CompositionMode.CompositionMode_Plus
                )
            )

        else:
            self.set_image(self._base_image)

    @QtCore.pyqtSlot(object)
    def set_image(self, image):
        """"""
        self.viewport_label.setPixmap(QtGui.QPixmap.fromImage(image))
