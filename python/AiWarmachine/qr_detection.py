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
"""QR detection object."""

import traceback
import copy
import time

import pyboof as pb
import numpy as np
from PyQt6 import QtCore, QtGui

from . import common


class QRDetector(QtCore.QThread):
    """Qr detector class to detect micro QR codes in image."""

    latest_data_ready = QtCore.pyqtSignal(dict, int, int, int, int)

    def __init__(self, core):
        """Initializer."""
        super().__init__()
        self.core = core
        self._detector = pb.FactoryFiducial(np.uint8).microqr()
        self._image_boof = None
        self._latest_data = {}
        self._image_np = None
        self._running = False
        self._overlay_image = self._get_empty_overlay(10, 10)
        self._is_processing = False

    def reset(self):
        """Reset the latest data."""
        self._latest_data = {}
        self._image_np = None

    @QtCore.pyqtSlot()
    def tick(self):
        """Get the latest frame and to a detection on it."""

    @property
    def data(self):
        """Get the detection data as """
        return copy.deepcopy(self._latest_data)

    def is_running(self):
        """Whether or not the detector is running."""
        return self._running

    def detect(self, np_image):
        """Detect Micro QR codes in image.

        :param np_image: Single band contiguous 3D array.
        :type np_image: :class:`NDArray`
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
            detections[qr.message] = {
                'bounds': vertices_pos_list,
                'pos': (sum_x / num_vertices, sum_y / num_vertices),
                'time': time.time()
            }
        return detections

    @QtCore.pyqtSlot(object, int, int, int, int)
    def set_image(self, image_np, min_x, min_y, max_x, max_y):
        """"""
        self._image_offset_x = min_x
        self._image_offset_y = min_y
        self._image_width = image_np.shape[1]
        self._image_height = image_np.shape[0]
        self._image_np = image_np[min_y:max_y, min_x:max_x]

    def _get_empty_overlay(self, width, height):
        """"""
        image_size = QtCore.QSize(width, height)
        image_overlay = QtGui.QImage(image_size, QtGui.QImage.Format.Format_ARGB32_Premultiplied)
        painter = QtGui.QPainter(image_overlay)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(image_overlay.rect(), QtCore.Qt.GlobalColor.transparent)
        painter.end()
        return image_overlay

    def get_image_overlay(self):
        """"""
        return self._overlay_image

    def stop(self):
        """"""
        self._running = False

    def run(self):
        """"""
        self._running = True
        while self._running:
            if self._image_np is not None:
                # overlay_offset_x = self._image_offset_x
                # overlay_offset_y = self._image_offset_y
                # overlay_width = self._image_width
                # overlay_height = self._image_height
                # overlay_image = self._get_empty_overlay(overlay_width, overlay_height)
                try:
                    detections = self.detect(np.copy(self._image_np))
                    self._latest_data.update(detections)
                    self.latest_data_ready.emit(self.data, self._image_offset_x, self._image_offset_y, self._image_width, self._image_height)
                    # if self._latest_data:
                    #     painter = QtGui.QPainter(overlay_image)
                    #     detect_brush = QtGui.QBrush()
                    #     painter.setBrush(detect_brush)
                    #     detect_pen = QtGui.QPen(QtCore.Qt.GlobalColor.red, 4, QtCore.Qt.PenStyle.SolidLine)
                    #     painter.setPen(detect_pen)
                    #     for qr_message, qr_data in self._latest_data.items():
                    #         for vert in qr_data['bounds']:
                    #             painter.drawEllipse(int(overlay_offset_x + vert[0]), int(overlay_offset_y + vert[1]), 5, 5)
                    #             break
                    #     painter.end()
                except Exception:
                    traceback.print_exc()
                    self._running = False
                # finally:
                #     self._overlay_image = overlay_image

            # QtCore.QCoreApplication.processEvents()
