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
"""The game table class contains everything related to the table, like play area dimension and terrain features."""

import re
import json

import numpy as np

from . import common


def get_reference_corner_3d_points(width, height):
    """Get the 4 corners 3d reference positions.

    :param width: Width of the table in inches. (30)
    :type width: int

    :param height: Height of the table in inches. (30)
    :type height: int

    :return: List of the 4 3d points (UL, UR, LR, LL) (4d homogenous).
    :rtype: list of :class:`np.ndarray`
    """
    w_2 = width / 2.0
    h_2 = height / 2.0
    return [
        np.array([[-w_2], [-h_2], [0.0], [1.0]], np.float32),
        np.array([[w_2], [-h_2], [0.0], [1.0]], np.float32),
        np.array([[w_2], [h_2], [0.0], [1.0]], np.float32),
        np.array([[-w_2], [h_2], [0.0], [1.0]], np.float32)
    ]


class GameTable(object):
    """The game table class."""

    def __init__(
        self,
        name="Latest",
        width=48,
        height=48,
        border_color_name="Yellow",
        alpha=255,
        tx=0.0,
        ty=0.0,
        tz=0.0,
        rx=0.0,
        ry=0.0,
        rz=0.0,
    ):
        """Initialize game table.

        :param name: A small name describing this table. ("Latest")
        :type name: str

        :param width: Width of the table in inches. (48)
        :type width: int

        :param height: Height of the table in inches. (48)
        :type height: int

        :param border_color_name: The border color name. ("Yellow")
        :type border_color_name: str

            .. note:: Valid choices are:
                -Black
                -Gray
                -White
                -Yellow
                -Orange
                -Red
                -Magenta
                -Purple
                -Blue
                -Cyan
                -Teal
                -Green
                -Lime

        :param alpha: The 8bit alpha value for the border color. (255)
        :type alpha: int

        :param tx: Translation X.
        :type tx: float

        :param ty: Translation Y.
        :type ty: float

        :param tz: Translation Z.
        :type tz: float

        :param rx: Rotation X.
        :type rx: float

        :param ry: Rotation Y.
        :type ry: float

        :param rz: Rotation X.
        :type rz: float
        """
        super().__init__()

        self.name = name
        self._width = width
        self._height = height
        self.set_border_color_from_name(border_color_name, alpha)
        self.set_transforms(tx, ty, tz, rx, ry, rz)

    @property
    def name(self):
        """Get the table name.

        :return: The name of the table.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, value):
        """Set the name of the table.

        :param value: The name of the table.
        :type value: str
        """
        self._name = value.strip() or "Latest"

    def set_border_color_from_name(self, border_color_name, alpha=255):
        """Update the border color of the table.

        :param border_color_name: The border color name.
        :type border_color_name: str

            .. note:: Valid choices are:
                -Black
                -Gray
                -White
                -Yellow
                -Orange
                -Red
                -Magenta
                -Purple
                -Blue
                -Cyan
                -Teal
                -Green
                -Lime

        :param alpha: The 8bit alpha value for the border color. (255)
        :type alpha: int
        """
        self._alpha = alpha
        self._border_color_name = border_color_name
        self.color = common.get_color_from_name(self._border_color_name, alpha=self._alpha)

    def get_border_color_name_and_alpha(self):
        """Get the boder color name and alpha value.

        :return: Color name and alpha.
        :rtype: tuple
        """
        return (self._border_color_name, self._alpha)

    def _update_corners(self):
        """Recalculate 3d positions of borders."""
        self._corners = []
        for corner in get_reference_corner_3d_points(self._width, self._height):
            mult_corner = np.matmul(self._matrix, corner)
            mult_corner /= mult_corner[3]
            self._corners.append(mult_corner[:3])

    def set_transforms(self, tx, ty, tz, rx, ry, rz):
        """Update the table transform matrix.

        :param tx: Translation X.
        :type tx: float

        :param ty: Translation Y.
        :type ty: float

        :param tz: Translation Z.
        :type tz: float

        :param rx: Rotation X.
        :type rx: float

        :param ry: Rotation Y.
        :type ry: float

        :param rz: Rotation X.
        :type rz: float
        """
        self._tx = tx
        self._ty = ty
        self._tz = tz
        self._rx = rx
        self._ry = ry
        self._rz = rz
        self._matrix = common.get_transform_matrix(tx, ty, tz, rx, ry, rz)
        self._update_corners()

    def get_transforms(self):
        """Get the translation and rotation xyz values.

        :return: Translate xyz and rotation xyz as a tuple of 6 values.
        :rtype: tuple
        """
        return (
            self._tx,
            self._ty,
            self._tz,
            self._rx,
            self._ry,
            self._rz
        )

    def get_transform_matrix(self):
        """Get the table transformation 4x4 matrix.

        :return: Transformation matrix.
        :rtype: :class:`ndarray`
        """
        return self._matrix.copy()

    def set_dimensions(self, width, height):
        """Set the table dimensions.

        :param width: Width of the table in inches.
        :type width: int

        :param height: Height of the table in inches.
        :type height: int
        """
        self._width = width
        self._height = height
        self._update_corners()

    def get_dimensions(self):
        """Get width and height values.

        :return: Width and height.
        :rtype: tuple
        """
        return (self._width, self._height)

    def get_corners(self):
        """Get the 3d positions of the 4 table corners in order: TL, TR, BR, BL, where T is top and B bottom.

        :return: List of 4 3d points.
        :rtype: list of :class:`np.ndarray`
        """
        return np.copy(self._corners)

    def get_save_filepath(self):
        """Get the filepath where the table file would be saved.

        :return: Filepath.
        :rtype: str
        """
        table_dir = common.get_saved_subdir("table")
        name = re.sub('[^a-zA-Z0-9]', '_', self.name)
        table_filename = f"{name}__{self._width}x{self._height}.json"
        table_filepath = f"{table_dir}/{table_filename}"

        return table_filepath

    def save(self, filepath):
        """Save the current dimension and  settings and calibration.

        :param filepath: The filepath to save the camera to.
        :type filepath: str
        """
        data = {
            'name': self.name,
            'width': self._width,
            'height': self._height,
            'border_color_name': self._border_color_name,
            'alpha': self._alpha,
            'tx': self._tx,
            'ty': self._ty,
            'tz': self._tz,
            'rx': self._rx,
            'ry': self._ry,
            'rz': self._rz,
        }

        with open(filepath, 'w') as fid:
            fid.write(json.dumps(data, indent=2))

    def load(self, table_data):
        """Load settings from a table file.

        :param filepath: The filepath to save the camera to.
        :type filepath: str
        """
        self.name = table_data['name']
        self._width = table_data['width']
        self._height = table_data['height']
        self.set_border_color_from_name(table_data['border_color_name'], table_data['alpha'])
        self.set_transforms(
            table_data['tx'],
            table_data['ty'],
            table_data['tz'],
            table_data['rx'],
            table_data['ry'],
            table_data['rz']
        )
