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
"""QR detection object."""

import copy
import time

import pyboof as pb
import numpy as np
from PyQt6 import QtCore

from . import constants


class QRDetector(QtCore.QObject):
    """Qr detector class to detect micro QR codes in image."""

    new_qr_detection_data = QtCore.pyqtSignal(dict)

    def __init__(self, core):
        """Initializer."""
        super().__init__()
        self.core = core
        self._detector = pb.FactoryFiducial(np.uint8).microqr()
        self._detection_data = {}

    @QtCore.pyqtSlot()
    def reset(self):
        """Reset the latest data."""
        self._detection_data = {}
        self.new_qr_detection_data.emit(copy.deepcopy(self._detection_data))

    def update_detection_data(self, detection_data, epsilon=constants.QR_CENTER_EPISLON):
        """Update previous detection data with new detections and emit new_qr_detection_data signal with copy of data.

        :param detection_data: New detection data.
        :type detection_data: dict

        :param epsilon: If center to center distance is less than this epsilon, do not consider as new detection. (constants.QR_CENTER_EPISLON)
        :type epsilon: float
        """
        has_changes = False
        for qr_message, data in detection_data.items():
            if qr_message not in self._detection_data:
                has_changes = True
                self._detection_data[qr_message] = data
            else:
                previous_x, previous_y = self._detection_data[qr_message]['pos']
                new_x, new_y = data['pos']
                if abs(previous_x - new_x) + abs(previous_y - new_y) > epsilon:
                    has_changes = True
                    self._detection_data[qr_message] = data
        if has_changes:
            self.new_qr_detection_data.emit(copy.deepcopy(self._detection_data))

    def detect(self, np_image):
        """Detect Micro QR codes in image.

        :param np_image: Single band contiguous 3D array.
        :type np_image: :class:`NDArray`

        :return: Game coordinates detections.
        :rtype: dict
        """
        image = pb.ndarray_to_boof(np_image)
        self._detector.detect(image)
        detections = {}
        for qr in self._detector.detections:
            vertices_pos_list = []
            sum_x, sum_y = 0.0, 0.0
            num_vertices = len(qr.bounds.vertexes)
            for vertex in qr.bounds.vertexes:
                sum_x += vertex.x
                sum_y += vertex.y
                vertices_pos_list.append((vertex.x, vertex.y))
            center_game_pos = self.core.game_table.warp_camera_position_to_game((sum_x / num_vertices, sum_y / num_vertices), rounded=True)
            detections[qr.message] = {
                'pos': center_game_pos,
                'time': time.time()
            }
        return detections

    @QtCore.pyqtSlot()
    def tick(self):
        """Get the latest frame and to a detection on it."""
        if not self.core.game_table.is_calibrated():
            return

        roi = self.core.game_table.get_camera_roi()

        np_image, _ = self.core.get_image(simply_latest_np_image=True)
        if np_image is None:
            return

        detections = self.detect(
            np.copy(
                np_image[
                    roi[constants.ROI_MIN_Y]:roi[constants.ROI_MAX_Y] + 1,
                    roi[constants.ROI_MIN_X]:roi[constants.ROI_MAX_X] + 1,
                    1
                ]
            )
        )

        self.update_detection_data(detections)

    # TODO: This should be moved to a different class as it depends of model base size.
    def query(self, pos, max_distance=30):
        """Get the data within a distance of the position.

        :param pos: A game position.
        :type pos: tuple[int]

        :param max_distance: The maximum manhattan length in pixels. (30)
        :type max_distance: int

        :return: QR message and position.
        :rtype: tuple[int, :class:`QPoint`]
        """
        for qr_message, qr_data in self._detection_data.items():
            if abs(pos[0] - qr_data['pos'][0]) + abs(pos[1] - qr_data['pos'][1]) <= max_distance:
                return qr_message, qr_data['pos']

        return None, None
