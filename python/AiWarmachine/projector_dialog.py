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
"""Projector dialog."""

from functools import partial

from PyQt6 import QtCore, QtWidgets, QtGui
import numpy as np
import cv2 as cv

from . import viewport_label, constants, common


class ProjectorDialog(QtWidgets.QDialog):
    """Projector dialog to draw information on board."""

    def __init__(self, core, main_dialog):
        """Initialize.

        :param core: The main core.
        :type core: :class:`MainCore`

        :param main_dialog: The parent widget.
        :type main_dialog: :class:`MainDialog`
        """
        super().__init__(parent=main_dialog, flags=QtCore.Qt.WindowType.WindowTitleHint | QtCore.Qt.WindowType.CustomizeWindowHint)
        self.core = core
        self.main_dialog = main_dialog
        self._is_fullscreen = False
        self._selected_corner_index = None
        self._selected_corner_offset = QtCore.QPoint(0, 0)
        self._corners_are_visible = False
        self._borders_in_bold = False

        self._detection_overlay_needs_update = True
        self._game_qr_detection_data = None
        self._qr_detection_overlay = None

        self._debug_overlay_needs_update = True
        self._debug_data = None
        self._debug_overlay = None

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

    def _init_connections(self):
        """Initialize the UI."""
        self.viewport_label.key_press_event.connect(self.process_viewport_keyboard_events)
        self.viewport_label.mouse_press_event.connect(partial(self.process_viewport_mouse_events, True))
        self.viewport_label.mouse_drag_event.connect(partial(self.process_viewport_mouse_events, False))

        # TODO: This should be moved to a different class
        self.core.qr_detector.new_qr_detection_data.connect(self.set_qr_detection_data)

    @QtCore.pyqtSlot(str)
    def process_viewport_keyboard_events(self, key_text):
        """Process key pressed events.

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
                self.tick()
                self.setGeometry(geometry.x() + 256, geometry.y() + 256, 480, 270)
            else:
                self.showFullScreen()
                size = self.geometry().size()
                self._base_image = self._base_image.scaled(
                    size.width(),
                    size.height(),
                    aspectRatioMode=QtCore.Qt.AspectRatioMode.IgnoreAspectRatio
                )
                self.tick()

            self._is_fullscreen = not self._is_fullscreen
            self.resize(self.viewport_label.sizeHint())

        elif key_text == "c":
            self._corners_are_visible = not self._corners_are_visible

        elif key_text == "b":
            self._borders_in_bold = not self._borders_in_bold

        elif key_text in constants.MOVE_KEY_POINTS_DICT and self._selected_corner_index is not None and self._corners_are_visible:
            width = self._base_image.width()
            height = self._base_image.height()

            corner_points_list = self.core.game_table.get_in_projector_corners_as_points()

            self.main_dialog.table_corners_widgets_dict['projector'][self._selected_corner_index][constants.TABLE_CORNERS_AXIS_X].setValue(
                min(max(0, corner_points_list[self._selected_corner_index].x() + constants.MOVE_KEY_POINTS_DICT[key_text].x()), width - 1)
            )
            self.main_dialog.table_corners_widgets_dict['projector'][self._selected_corner_index][constants.TABLE_CORNERS_AXIS_Y].setValue(
                min(max(0, corner_points_list[self._selected_corner_index].y() + constants.MOVE_KEY_POINTS_DICT[key_text].y()), height - 1)
            )

    @QtCore.pyqtSlot(bool, float, float)
    def process_viewport_mouse_events(self, is_pressed, norm_pos_x, norm_pos_y):
        """Process mouse event from the viewport.

        This function deals with table corners values for example.

        :param is_press: Whether this is a press event instead of a drag.
        :type is_press: bool

        :param norm_pos_x: Position relative to viewport width as [0, 1[.
        :type norm_pos_x: float

        :param norm_pos_x: Position relative to viewport height as [0, 1[.
        :type norm_pos_x: float
        """
        if not self._corners_are_visible:
            return

        width = self._base_image.width()
        height = self._base_image.height()

        corner_points_list = self.core.game_table.get_in_projector_corners_as_points()

        if is_pressed:
            pos_mouse = QtCore.QPoint(int(norm_pos_x * width), int(norm_pos_y * height))
            self._selected_corner_index = None
            closest_corner_index = None
            closest_distance = None

            for corner_index in constants.TABLE_CORNERS_DRAWING_ORDER:
                test_pos = corner_points_list[corner_index] - pos_mouse
                test_distance = test_pos.manhattanLength()
                if (
                    test_distance < constants.MAXIMUM_CLOSEST_TABLE_CORNERS_DISTANCE and
                    (
                        closest_distance is None or
                        test_distance < closest_distance
                    )
                ):
                    closest_corner_index = corner_index
                    closest_distance = test_distance

            if closest_corner_index is not None:
                self._selected_corner_index = closest_corner_index
                self._selected_corner_offset = corner_points_list[closest_corner_index] - pos_mouse

        elif self._selected_corner_index is not None:
            self.main_dialog.table_corners_widgets_dict['projector'][self._selected_corner_index][constants.TABLE_CORNERS_AXIS_X].setValue(
                min(max(0, int(norm_pos_x * width) + self._selected_corner_offset.x()), width - 1)
            )
            self.main_dialog.table_corners_widgets_dict['projector'][self._selected_corner_index][constants.TABLE_CORNERS_AXIS_Y].setValue(
                min(max(0, int(norm_pos_y * height) + self._selected_corner_offset.y()), height - 1)
            )

    def tick(self):
        """Refresh viewport."""
        image = self._base_image
        # Corners
        if self._corners_are_visible:
            corners_overlay, corners_overlay_roi = self.core.game_table.get_projector_corners_overlay(bold=self._borders_in_bold)
            if corners_overlay is not None:
                image = common.composite_images(self._base_image, corners_overlay, corners_overlay_roi[constants.ROI_MIN_X], corners_overlay_roi[constants.ROI_MIN_Y])

        # QR Detection
        if self._detection_overlay_needs_update and self._game_qr_detection_data is not None:
            self._qr_detection_overlay = self.create_game_qr_detection_overlay()
            self._detection_overlay_needs_update = False

        if self._qr_detection_overlay is not None:
            roi = self.core.game_table.get_projector_roi()
            if roi is not None:
                image = common.composite_images(
                    image,
                    self._qr_detection_overlay,
                    roi[constants.ROI_MIN_X],
                    roi[constants.ROI_MIN_Y],
                    composite_mode=QtGui.QPainter.CompositionMode.CompositionMode_Plus
                )

        # Debug
        if self._debug_overlay_needs_update and self._debug_data is not None:
            self._debug_overlay = self.core.game_table.create_debug_overlay(
                debug_data=self._debug_data,
                is_projector=True
            )
            self._debug_overlay_needs_update = False

        if self._debug_overlay is not None:
            roi = self.core.game_table.get_projector_roi()
            if roi is not None:
                image = common.composite_images(
                    image,
                    self._debug_overlay,
                    roi[constants.ROI_MIN_X],
                    roi[constants.ROI_MIN_Y],
                    composite_mode=QtGui.QPainter.CompositionMode.CompositionMode_Plus
                )

        self.set_image(image)

    @QtCore.pyqtSlot(QtGui.QImage)
    def set_image(self, image):
        """Set viewpost image.

        :param image: The image.
        :type image: :class:`QImage`
        """
        self.viewport_label.setPixmap(QtGui.QPixmap.fromImage(image))

    # Debug
    @QtCore.pyqtSlot(dict)
    def set_debug_data(self, data):
        """Notify of new debug data.

        :param data: Debug data.
        :type data: dict
        """
        if self.core.game_table.is_calibrated():
            self._debug_data = data
            self._debug_overlay_needs_update = True

    # TODO: This should be moved to a different class as it depends of model base size.
    @QtCore.pyqtSlot(dict)
    def set_qr_detection_data(self, game_qr_detection_data):
        """Notify of new qr detection data and prepare to create new overlay."""
        self._game_qr_detection_data = game_qr_detection_data
        self._detection_overlay_needs_update = True

    def create_game_qr_detection_overlay(self):
        """Create game overlay to composite in plus mode.

        :return: QR Detection overlay.
        :rtype: :class:`QImage`
        """
        width, height = self.core.game_table.get_effective_table_image_size()
        image = np.zeros(
            (
                height,
                width,
                3
            ),
            dtype=np.uint8
        )
        small_base_radius = self.core.game_table.convert_mm_to_pixel(15 + 3, rounded=True)
        thickness = self.core.game_table.convert_mm_to_pixel(2, ceiled=True)

        for qr_data in self._game_qr_detection_data.values():
            cv.circle(
                image,
                qr_data['pos'],
                small_base_radius,
                (255, 255, 255),
                thickness
            )

        warped_image = self.core.game_table.warp_game_to_projector_image(image)
        return QtGui.QImage(
            warped_image,
            warped_image.shape[1],
            warped_image.shape[0],
            warped_image.strides[0],
            QtGui.QImage.Format.Format_BGR888
        )
