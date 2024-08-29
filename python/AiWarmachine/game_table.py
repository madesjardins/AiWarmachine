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
"""The game table module contains everything related to the table, like play area dimension."""

import re
import json
import copy
import math

import cv2 as cv
import numpy as np
from PyQt6 import QtCore, QtGui

from . import common, constants


class GameTable(QtCore.QObject):
    """The game table class."""

    def __init__(
        self,
        name="Latest",
        width=914.4,
        height=609.6,
        resolution_factor=2,
        in_camera_corners=None,
        in_projector_corners=None,
        camera_to_game_matrix=None,
        game_to_projector_matrix=None,
    ):
        """Initialize game table.

        :param name: A small name describing this table. ("Latest")
        :type name: str

        :param width: Width of the table in mm. (914.4)
        :type width: float

        :param height: Height of the table in mm. (609.6)
        :type height: float

        :param resolution_factor: Precision of the table projector image in px/mm. (2)
        :type resolution_factor: int

        :param in_camera_corners: The table corners as seen by the camera in order BL, TL, TR, BR.
        :type in_camera_corners: list[list[int]]

        :param in_projector_corners: The table corners as seen by the projector in order BL, TL, TR, BR.
        :type in_projector_corners: list[list[int]]
        """
        super().__init__()

        self._name = name
        self._width = width
        self._height = height
        self._resolution_factor = resolution_factor
        self._corners_list = [in_camera_corners, in_projector_corners]
        self._camera_to_game_matrix = camera_to_game_matrix
        self._game_to_projector_matrix = game_to_projector_matrix

        self._roi = [None, None]
        self._adjusted_roi = [None, None]
        self._corners_overlay_needs_update = [True, True]
        self._corners_overlay = [None, None]

        for corners_type in [constants.TABLE_CORNERS_TYPE_CAMERA, constants.TABLE_CORNERS_TYPE_PROJECTOR]:
            if self._corners_list[corners_type] is None:
                self._corners_list[corners_type] = [
                    [100, 980],
                    [100, 100],
                    [1800, 100],
                    [1800, 980]
                ]

            self._update_roi(corners_type)

        if self._camera_to_game_matrix is None or self._game_to_projector_matrix is None:
            self._camera_to_game_matrix = None
            self._game_to_projector_matrix = None

        self.disable_slots = False

    # ######################
    #
    # GENERAL
    #
    # ######################
    @QtCore.pyqtSlot(str)
    def set_name(self, value):
        """Set the name of the table.

        :param value: The name of the table.
        :type value: str
        """
        if self.disable_slots:
            return
        self._name = value.strip() or "Latest"

    @QtCore.pyqtSlot(float)
    def set_width(self, value):
        """Set the table width.

        :param value: The width in mm.
        :type value: float
        """
        if self.disable_slots:
            return
        self._width = value

    @QtCore.pyqtSlot(float)
    def set_height(self, value):
        """Set the table height.

        :param value: The height in mm.
        :type value: float
        """
        if self.disable_slots:
            return
        self._height = value

    @QtCore.pyqtSlot(int)
    def set_resolution_factor(self, value):
        """Set the resolution factor.

        :param value: The resolution factor in px/mm.
        :type value: int
        """
        if self.disable_slots:
            return
        self._resolution_factor = value

    def _update_roi(self, corners_type):
        """Calculate and update the ROI for the camera/projector view.

        :param corners_type: The corner type in constants.TABLE_CORNERS_TYPE_*, where * is in [CAMERA, PROJECTOR].
        :type corners_type: int
        """
        min_x = min([_p[constants.TABLE_CORNERS_AXIS_X] for _p in self._corners_list[corners_type]])
        min_y = min([_p[constants.TABLE_CORNERS_AXIS_Y] for _p in self._corners_list[corners_type]])
        max_x = max([_p[constants.TABLE_CORNERS_AXIS_X] for _p in self._corners_list[corners_type]])
        max_y = max([_p[constants.TABLE_CORNERS_AXIS_Y] for _p in self._corners_list[corners_type]])
        self._roi[corners_type] = [min_x, min_y, max_x, max_y]

    @QtCore.pyqtSlot(int, int, int, int)
    def set_corner_position(self, corner_type, corner_index, axis, value):
        """Update the corner position.

        :param corner_type: The corner type in constants.TABLE_CORNERS_TYPE_*, where * is in [CAMERA, PROJECTOR].
        :type corner_type: int

        :param corner_index: The index of the corner TABLE_CORNERS_INDEX_*, where * is in [BL, TL, TR, BR].
        :type corner_index: int

        :param axis: The axis for this value TABLE_CORNERS_AXIS_*, where * is in [X, Y].
        :type axis: int

        :param value: The value.
        :type value: int
        """
        if self.disable_slots:
            return
        self._corners_list[corner_type][corner_index][axis] = value
        self._corners_overlay_needs_update[corner_type] = True
        self._update_roi(corner_type)

    def get_data(self):
        """Get all important serializable data.

        :return: The data.
        :rtype: dict
        """
        if self._camera_to_game_matrix is not None:
            camera_to_game_matrix = self._camera_to_game_matrix.tolist()
        else:
            camera_to_game_matrix = None

        if self._game_to_projector_matrix is not None:
            game_to_projector_matrix = self._game_to_projector_matrix.tolist()
        else:
            game_to_projector_matrix = None

        return {
            'name': self._name,
            'width': self._width,
            'height': self._height,
            'resolution_factor': self._resolution_factor,
            'in_camera_corners': self._corners_list[constants.TABLE_CORNERS_TYPE_CAMERA],
            'in_projector_corners': self._corners_list[constants.TABLE_CORNERS_TYPE_PROJECTOR],
            'camera_to_game_matrix': camera_to_game_matrix,
            'game_to_projector_matrix': game_to_projector_matrix,
            'camera_roi': self._roi[constants.TABLE_CORNERS_TYPE_CAMERA],
            'adjusted_camera_roi': self._adjusted_roi[constants.TABLE_CORNERS_TYPE_CAMERA],
            'projector_roi': self._roi[constants.TABLE_CORNERS_TYPE_PROJECTOR],
            'adjusted_projector_roi': self._adjusted_roi[constants.TABLE_CORNERS_TYPE_PROJECTOR]
        }

    def save(self, filepath):
        """Save the current table in a JSON.

        :param filepath: The filepath to save the table to.
        :type filepath: str
        """
        with open(filepath, 'w') as fid:
            fid.write(json.dumps(self.get_data(), indent=2))

    def load(self, filepath):
        """Load from a table file.

        :param filepath: The JSON filepath to load the table from.
        :type filepath: str
        """
        with open(filepath, 'r') as fid:
            table_data = json.loads(fid.read())

        self._name = table_data['name']
        self._width = table_data['width']
        self._height = table_data['height']
        self._resolution_factor = table_data['resolution_factor']
        self._corners_list = [table_data['in_camera_corners'], table_data['in_projector_corners']]

        if table_data['camera_to_game_matrix'] is None:
            self._camera_to_game_matrix = None
        else:
            self._camera_to_game_matrix = cv.Mat(np.float32(table_data['camera_to_game_matrix']))

        if table_data['game_to_projector_matrix'] is None:
            self._game_to_projector_matrix = None
        else:
            self._game_to_projector_matrix = cv.Mat(np.float32(table_data['game_to_projector_matrix']))

        self._roi = [table_data['camera_roi'], table_data['projector_roi']]
        self._adjusted_roi = [table_data['adjusted_camera_roi'], table_data['adjusted_projector_roi']]
        self._corners_overlay_needs_update = [True, True]
        self._corners_overlay = [None, None]

    def get_effective_table_image_size(self):
        """Get the effective table size in pixels using the resolution factor.

        :return: Width and height.
        :rtype: tuple(int, int)
        """
        width = self.convert_mm_to_pixel(self._width, ceiled=True)
        height = self.convert_mm_to_pixel(self._height, ceiled=True)
        return width, height

    def get_reference_corner_2d_points(self):
        """Get the 4 corners 2d reference positions.

        :return: Array of 4 2d points (BL, TL, TR, BR).
        :rtype: :class:`np.ndarray`
        """
        width = self.convert_mm_to_pixel(self._width)
        height = self.convert_mm_to_pixel(self._height)
        return np.float32(
            [
                [0.0, 0.0],
                [0.0, height],
                [width, height],
                [width, 0.0]
            ]
        )

    def is_calibrated(self):
        """Whether or not this table is calibrated."""
        return (self._camera_to_game_matrix is not None and self._game_to_projector_matrix is not None)

    def calibrate(self):
        """Calculate the perspective transform matrices for camera -> game and game -> projector."""
        self._update_roi(constants.TABLE_CORNERS_TYPE_CAMERA)
        self._update_roi(constants.TABLE_CORNERS_TYPE_PROJECTOR)

        game_points = self.get_reference_corner_2d_points()

        camera_points = np.float32([
            [
                _p[0] - self._roi[constants.TABLE_CORNERS_TYPE_CAMERA][constants.ROI_MIN_X],
                _p[1] - self._roi[constants.TABLE_CORNERS_TYPE_CAMERA][constants.ROI_MIN_Y]
            ]
            for _p in self._corners_list[constants.TABLE_CORNERS_TYPE_CAMERA]
        ])
        projector_points = np.float32([
            [
                _p[0] - self._roi[constants.TABLE_CORNERS_TYPE_PROJECTOR][constants.ROI_MIN_X],
                _p[1] - self._roi[constants.TABLE_CORNERS_TYPE_PROJECTOR][constants.ROI_MIN_Y]
            ]
            for _p in self._corners_list[constants.TABLE_CORNERS_TYPE_PROJECTOR]
        ])

        self._camera_to_game_matrix = cv.getPerspectiveTransform(camera_points, game_points)
        self._game_to_projector_matrix = cv.getPerspectiveTransform(game_points, projector_points)

    def uncalibrate(self):
        """Reset perspective transform matrices for camera -> game and game -> projector."""
        self._camera_to_game_matrix = None
        self._game_to_projector_matrix = None

    def get_save_filepath(self):
        """Get the filepath where the table file would be saved.

        :return: Filepath.
        :rtype: str
        """
        table_dir = common.get_saved_subdir("table")
        name = re.sub('[^a-zA-Z0-9]', '_', self._name)
        table_filename = f"{name}.json"
        table_filepath = f"{table_dir}/{table_filename}"

        return table_filepath

    def get_corners_overlay(self, corners_type, bold=False):
        """Get the camera/projector corners overlay.

            Will only get redrawn if it needs to, other wise, it will send previous one.

        :param corners_type: The corners type in constants.TABLE_CORNERS_TYPE_*, where * is in [CAMERA, PROJECTOR].
        :type corners_type: int

        :param bold: Whether or not to draw bold table borders. (False)
        :param bold: bool

        :return: Image and ROI.
        :rtype: tuple[:class:`QImage`, tuple[int, int, int, int]]
        """
        if self._corners_overlay[corners_type] is not None and not self._corners_overlay_needs_update[corners_type]:
            return self._corners_overlay[corners_type], self._adjusted_roi[corners_type]

        # adjust for corner circle
        self._adjusted_roi[corners_type] = [
            max(0, self._roi[corners_type][constants.ROI_MIN_X] - 12),
            max(0, self._roi[corners_type][constants.ROI_MIN_Y] - 12),
            self._roi[corners_type][constants.ROI_MAX_X] + 12,
            self._roi[corners_type][constants.ROI_MAX_Y] + 12
        ]

        overlay_width = self._adjusted_roi[corners_type][constants.ROI_MAX_X] - self._adjusted_roi[corners_type][constants.ROI_MIN_X] + 1
        overlay_height = self._adjusted_roi[corners_type][constants.ROI_MAX_Y] - self._adjusted_roi[corners_type][constants.ROI_MIN_Y] + 1
        if (
            self._corners_overlay[corners_type] is None or
            self._corners_overlay[corners_type].width() != overlay_width or
            self._corners_overlay[corners_type].height() != overlay_height
        ):
            image_size = QtCore.QSize(overlay_width, overlay_height)
            self._corners_overlay[corners_type] = QtGui.QImage(image_size, QtGui.QImage.Format.Format_ARGB32_Premultiplied)

        painter = QtGui.QPainter(self._corners_overlay[corners_type])
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self._corners_overlay[corners_type].rect(), QtCore.Qt.GlobalColor.transparent)
        pen_size = 5 if bold else 1
        brush = QtGui.QBrush()
        painter.setBrush(brush)
        pen = QtGui.QPen(QtCore.Qt.GlobalColor.white, pen_size, QtCore.Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        polyline_points_list = []
        for corner_id in constants.TABLE_CORNERS_DRAWING_ORDER:
            polyline_points_list.append(
                QtCore.QPoint(
                    self._corners_list[corners_type][corner_id][constants.TABLE_CORNERS_AXIS_X] - self._adjusted_roi[corners_type][constants.ROI_MIN_X],
                    self._corners_list[corners_type][corner_id][constants.TABLE_CORNERS_AXIS_Y] - self._adjusted_roi[corners_type][constants.ROI_MIN_Y]
                )
            )
        # Need the first in last to to close
        polyline_points_list.append(polyline_points_list[0])
        painter.drawPolyline(polyline_points_list)
        if not self.is_calibrated():
            # Draw corner ellipse when not calibrated
            for corner_id in constants.TABLE_CORNERS_DRAWING_ORDER:
                painter.setPen(QtGui.QPen(constants.TABLE_CORNERS_INDEX_TO_COLOR[corner_id], 2, QtCore.Qt.PenStyle.SolidLine))
                painter.drawEllipse(polyline_points_list[corner_id], 10, 10)
        painter.end()

        return self._corners_overlay[corners_type], self._adjusted_roi[corners_type]

    def get_corners_as_points(self, corners_type):
        """Get the in camera/projector corners as a list of QPoints.

        :param corners_type: The corners type in constants.TABLE_CORNERS_TYPE_*, where * is in [CAMERA, PROJECTOR].
        :type corners_type: int

        :return: List of ordered points.
        :rtype: list[:class:`QPoint`]
        """
        qpoints_list = []
        for posx, posy in self._corners_list[corners_type]:
            qpoints_list.append(QtCore.QPoint(posx, posy))
        return qpoints_list

    def convert_mm_to_pixel(self, value, rounded=False, ceiled=False, floored=False):
        """Convert a length in mm to pixel.

            .. note:: Only one of the arguments rounded, ceiled or floored will be used in that priority order.

        :param value: The value in mm to convert to pixel.
        :type value: float

        :param rounded: Whether or not to return the integer rounded value or not. (True)
        :type rounded: bool

        :param ceiled: Whether or not to return the integer ceiling of the value or not. (False)
        :type ceiled: bool

        :param floored: Whether or not to return the integer floor of the value or not. (False)
        :type floored: bool

        :return: The value in pixels.
        :rtype: float
        """
        converted_value = value * self._resolution_factor
        if rounded:
            return round(converted_value)
        elif ceiled:
            return math.ceil(converted_value)
        elif floored:
            return math.floor(converted_value)
        else:
            return converted_value

    def convert_pixel_to_mm(self, value):
        """Convert a length in pixel to mm.

        :param value: The value in mm to convert to pixel.
        :type value: float

        :return: The value in mm.
        :rtype: float
        """
        return value / self._resolution_factor

    def create_debug_overlay(self, debug_data, is_projector=False):
        """Create debug overlay for camera or projector to composite in plus mode.

        :param debug_data: The debug data to show.
        :type debug_data: dict

        :param is_projector: If set to True, will create overlay for projector instead of camera. (False)
        :type is_projector: bool

        :return: QR Detection overlay.
        :rtype: :class:`QImage`
        """
        if not debug_data or not self.is_calibrated():
            return None

        width, height = self.get_effective_table_image_size()

        image = np.zeros(
            (
                height,
                width,
                3
            ),
            dtype=np.uint8
        )

        if test_position_data := debug_data.get('test_position'):

            thickness = test_position_data['thickness']
            size = test_position_data['size']

            cv.line(
                image,
                (test_position_data['pos'][0] - size, test_position_data['pos'][1]),
                (test_position_data['pos'][0] + size, test_position_data['pos'][1]),
                (255, 255, 255),
                thickness
            )
            cv.line(
                image,
                (test_position_data['pos'][0], test_position_data['pos'][1] - size),
                (test_position_data['pos'][0], test_position_data['pos'][1] + size),
                (255, 255, 255),
                thickness
            )

        if is_projector:
            warped_image = self.warp_game_to_projector_image(image)
        else:
            warped_image = self.warp_game_to_camera_image(image)

        return QtGui.QImage(
            warped_image,
            warped_image.shape[1],
            warped_image.shape[0],
            warped_image.strides[0],
            QtGui.QImage.Format.Format_BGR888
        )

    # ######################
    #
    # CAMERA
    #
    # ######################
    def get_camera_corners_overlay(self, bold=False):
        """Get the camera corners overlay.

            Will only get redrawn if it needs to, other wise, it will send previous one.

        :param bold: Whether or not to draw bold table borders. (False)
        :param bold: bool

        :return: Image and ROI.
        :rtype: tuple[:class:`QImage`, tuple[int, int, int, int]]
        """
        return self.get_corners_overlay(corners_type=constants.TABLE_CORNERS_TYPE_CAMERA, bold=bold)

    def get_in_camera_corners_as_points(self):
        """Get the in camera corners as a list of QPoints.

        :return: List of ordered points.
        :rtype: list[:class:`QPoint`]
        """
        return self.get_corners_as_points(constants.TABLE_CORNERS_TYPE_CAMERA)

    def set_camera_corners_overlay_needs_update(self):
        """Set the flag to redraw the camera overlay."""
        self._corners_overlay_needs_update[constants.TABLE_CORNERS_TYPE_CAMERA] = True

    def get_camera_roi(self):
        """Get the camera ROI.

        :return: ROI values [min_x, min_y, max_x, max_y].
        :rtype: list[int]
        """
        camera_roi = self._roi[constants.TABLE_CORNERS_TYPE_CAMERA]
        if not self.is_calibrated() or camera_roi is None:
            return None

        return copy.deepcopy(camera_roi)

    def warp_camera_position_to_game(self, pos, rounded=False):
        """Warp a 2D in camera roi position to game position.

        :param pos: The (x, y) position.
        :type pos: tuple[float]

        :param rounded: Whether or not to round the result and return integers. (False)
        :type rounded: bool

        :return: Warped position.
        :rtype: tuple[float]
        """
        pos_homo = np.float32([pos[0], pos[1], 1.0])
        warp_pos_homo = self._camera_to_game_matrix.dot(pos_homo)
        warp_pos = (warp_pos_homo / warp_pos_homo[2])[:2]
        if rounded:
            return (round(warp_pos[0]), round(warp_pos[1]))
        else:
            return warp_pos

    def warp_game_position_to_camera(self, pos, rounded=False):
        """Warp a 2D in camera roi position to game position.

        :param pos: The (x, y) position.
        :type pos: tuple[float]

        :param rounded: Whether or not to round the result and return integers. (False)
        :type rounded: bool

        :return: Warped position.
        :rtype: tuple[float]
        """

        pos_homo = np.float32([pos[0], pos[1], 1.0])
        warp_pos_homo = np.linalg.inv(self._camera_to_game_matrix).dot(pos_homo)
        warp_pos = (warp_pos_homo / warp_pos_homo[2])[:2]
        if rounded:
            return (round(warp_pos[0]), round(warp_pos[1]))
        else:
            return warp_pos

    def warp_game_to_camera_image(self, image):
        """Warp an image using the game -> image perspective transform.

        :param image: Numpy image.
        :type: :class:`NDArray`

        :return: Warped image.
        :rtype: :class:`NDArray`
        """
        camera_roi = self._roi[constants.TABLE_CORNERS_TYPE_CAMERA]
        width = camera_roi[constants.ROI_MAX_X] - camera_roi[constants.ROI_MIN_X] + 1
        height = camera_roi[constants.ROI_MAX_Y] - camera_roi[constants.ROI_MIN_Y] + 1
        return cv.warpPerspective(image, self._camera_to_game_matrix, (width, height), flags=cv.WARP_INVERSE_MAP)

    # ######################
    #
    # PROJECTOR
    #
    # ######################
    def get_projector_corners_overlay(self, bold=False):
        """Get the projector corners overlay.

            Will only get redrawn if it needs to, other wise, it will send previous one.

        :param bold: Whether or not to draw bold table borders. (False)
        :param bold: bool

        :return: Image and ROI.
        :rtype: tuple[:class:`QImage`, tuple[int, int, int, int]]
        """
        return self.get_corners_overlay(corners_type=constants.TABLE_CORNERS_TYPE_PROJECTOR, bold=bold)

    def get_in_projector_corners_as_points(self):
        """Get the in projector corners as a list of QPoints.

        :return: List of ordered points.
        :rtype: list[:class:`QPoint`]
        """
        return self.get_corners_as_points(constants.TABLE_CORNERS_TYPE_PROJECTOR)

    def set_projector_corners_overlay_needs_update(self):
        """Set the flag to redraw the projector overlay."""
        self._corners_overlay_needs_update[constants.TABLE_CORNERS_TYPE_PROJECTOR] = True

    def get_projector_roi(self):
        """Get the projector ROI.

        :return: ROI values [min_x, min_y, max_x, max_y].
        :rtype: list[int]
        """
        projector_roi = self._roi[constants.TABLE_CORNERS_TYPE_PROJECTOR]
        if not self.is_calibrated() or projector_roi is None:
            return None

        return copy.deepcopy(projector_roi)

    def warp_game_to_projector_image(self, image):
        """Warp an image using the game -> projector perspective transform.

        :param image: Numpy image.
        :type: :class:`NDArray`

        :return: Warped image.
        :rtype: :class:`NDArray`
        """
        projector_roi = self._roi[constants.TABLE_CORNERS_TYPE_PROJECTOR]
        width = projector_roi[constants.ROI_MAX_X] - projector_roi[constants.ROI_MIN_X] + 1
        height = projector_roi[constants.ROI_MAX_Y] - projector_roi[constants.ROI_MIN_Y] + 1
        return cv.warpPerspective(image, self._game_to_projector_matrix, (width, height))
