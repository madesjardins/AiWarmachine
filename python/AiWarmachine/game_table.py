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
"""The game table class contains everything related to the table, like play area dimension.

we assume the
"""

import re
import json

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

        :param resolution_factor: Precision of the table projector image in mm/px. (2)
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
        self._in_camera_corners = in_camera_corners
        self._in_projector_corners = in_projector_corners
        self._camera_to_game_matrix = camera_to_game_matrix
        self._game_to_projector_matrix = game_to_projector_matrix

        if self._in_camera_corners is None:
            self._in_camera_corners = [
                [100, 1800],
                [100, 100],
                [1800, 100],
                [1800, 1800]
            ]

        if self._in_projector_corners is None:
            self._in_projector_corners = [
                [100, 1800],
                [100, 100],
                [1800, 100],
                [1800, 1800]
            ]

        self._camera_roi = self._update_camera_roi()

        if self._camera_to_game_matrix is None or self._game_to_projector_matrix is None:
            self._camera_to_game_matrix = None
            self._game_to_projector_matrix = None

        self._camera_corners_overlay_needs_update = True
        self._camera_corners_overlay = None

        self.disable_slots = False

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

        :param value: The resolution factor in mm/px.
        :type value: int
        """
        if self.disable_slots:
            return
        self._resolution_factor = value

    @QtCore.pyqtSlot(int)
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

        if corner_type == constants.TABLE_CORNERS_TYPE_CAMERA:
            corners_list = self._in_camera_corners
        else:
            corners_list = self._in_projector_corners

        corners_list[corner_index][axis] = value
        self._camera_corners_overlay_needs_update = True
        self._update_camera_roi()

    def _update_camera_roi(self):
        """Calculate and update the ROI for the camera view."""
        min_x = min([_p[constants.TABLE_CORNERS_AXIS_X] for _p in self._in_camera_corners])
        min_y = min([_p[constants.TABLE_CORNERS_AXIS_Y] for _p in self._in_camera_corners])
        max_x = max([_p[constants.TABLE_CORNERS_AXIS_X] for _p in self._in_camera_corners])
        max_y = max([_p[constants.TABLE_CORNERS_AXIS_Y] for _p in self._in_camera_corners])
        self._camera_roi = [min_x, min_y, max_x, max_y]

    def get_reference_corner_2d_points(self):
        """Get the 4 corners 2d reference positions.

        :return: Array of 4 2d points (BL, TL, TR, BR).
        :rtype: :class:`np.ndarray`
        """
        return np.float32(
            [
                [0.0, 0.0],
                [0.0, self._height],
                [self._width, self._height],
                [self._width, 0.0]
            ]
        )

    def is_calibrated(self):
        """Whether or not this table is calibrated."""
        return (self._camera_to_game_matrix is not None and self._game_to_projector_matrix is not None)

    def calibrate(self):
        """Calculate the perspective transform matrices for camera -> game and game -> projector."""
        self._update_camera_roi()
        game_points = self.get_reference_corner_2d_points()
        camera_points = np.float32(self._in_camera_corners)
        projector_points = np.float32(self._in_projector_corners)
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

    def get_camera_corners_overlay(self):
        """Get the camera corners overlay.

            Will only get redrawn if it needs to, other wise, it will send previous one.

        :return: Image and ROI.
        :rtype: tuple[:class:`QImage`, tuple[int, int, int, int]]
        """
        if self._camera_corners_overlay is not None and not self._camera_corners_overlay_needs_update:
            return self._camera_corners_overlay, self._adjusted_camera_roi

        # adjust for corner circle
        self._adjusted_camera_roi = [
            max(0, self._camera_roi[0] - 12),
            max(0, self._camera_roi[1] - 12),
            self._camera_roi[2] + 12,
            self._camera_roi[3] + 12
        ]

        overlay_width = self._adjusted_camera_roi[2] - self._adjusted_camera_roi[0] + 1
        overlay_height = self._adjusted_camera_roi[3] - self._adjusted_camera_roi[1] + 1
        if (
            self._camera_corners_overlay is None or
            self._camera_corners_overlay.width() != overlay_width or
            self._camera_corners_overlay.height() != overlay_height
        ):
            image_size = QtCore.QSize(overlay_width, overlay_height)
            self._camera_corners_overlay = QtGui.QImage(image_size, QtGui.QImage.Format.Format_ARGB32_Premultiplied)

        painter = QtGui.QPainter(self._camera_corners_overlay)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self._camera_corners_overlay.rect(), QtCore.Qt.GlobalColor.transparent)

        brush = QtGui.QBrush()
        painter.setBrush(brush)
        pen = QtGui.QPen(QtCore.Qt.GlobalColor.white, 1, QtCore.Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        polyline_points_list = []
        for corner_id in constants.TABLE_CORNERS_DRAWING_ORDER:
            polyline_points_list.append(
                QtCore.QPoint(
                    self._in_camera_corners[corner_id][0] - self._adjusted_camera_roi[0],
                    self._in_camera_corners[corner_id][1] - self._adjusted_camera_roi[1]
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
        return self._camera_corners_overlay, self._adjusted_camera_roi

    def get_in_camera_corners_as_points(self):
        """Get the in camera corners as a list of QPoints.

        :return: List of ordered points.
        :rtype: list[:class:`QPoint`]
        """
        qpoints_list = []
        for posx, posy in self._in_camera_corners:
            qpoints_list.append(QtCore.QPoint(posx, posy))
        return qpoints_list

    def set_camera_corners_overlay_needs_update(self):
        """Set the flag to redraw the camera overlay."""
        self._camera_corners_overlay_needs_update = True

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
            'in_camera_corners': self._in_camera_corners,
            'in_projector_corners': self._in_projector_corners,
            'camera_to_game_matrix': camera_to_game_matrix,
            'game_to_projector_matrix': game_to_projector_matrix,
            'camera_roi': self._camera_roi,
            'adjusted_camera_roi': self._adjusted_camera_roi
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
        self._in_camera_corners = table_data['in_camera_corners']
        self._in_projector_corners = table_data['in_projector_corners']
        if table_data['camera_to_game_matrix'] is None:
            self._camera_to_game_matrix = None
        else:
            self._camera_to_game_matrix = cv.Mat(np.float32(table_data['camera_to_game_matrix']))

        if table_data['game_to_projector_matrix'] is None:
            self._game_to_projector_matrix = None
        else:
            self._game_to_projector_matrix = cv.Mat(np.float32(table_data['game_to_projector_matrix']))

        self._camera_roi = table_data['camera_roi']
        self._adjusted_camera_roi = table_data['adjusted_camera_roi']
        self._camera_corners_overlay = None
        self._camera_corners_overlay_needs_update = True
