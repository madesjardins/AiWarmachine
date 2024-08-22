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
"""Core module for the main dialog to setup camera and table."""

import time

from PyQt6 import QtCore, QtGui

from . import constants, camera_manager, camera_calibration, common


class MainCore(QtCore.QObject):
    """Core class behind the main dialog."""

    def __init__(self):
        """Initialize."""
        super().__init__()

        self._tps = constants.DEFAULT_TICKS_PER_SECONDS
        self._tick_interval = 1.0 / self._tps

        self.latest_image = None
        self._previous_processing_time = 0
        self._safe_image_grab_coefficient = 1
        self._animation_frame = 0

        self._qrdps = constants.DEFAULT_QR_DETECTION_PER_SECONDS
        self._qrd_interval = 1.0 / self._qrdps

        self.camera_manager = camera_manager.CameraManager()
        self.camera_calibration_helper = camera_calibration.CameraCalibrationHelper()

        self._init_tickers()

    def _init_tickers(self):
        """Initialize the different tickers."""
        self.refresh_ticker = QtCore.QTimer()
        self.refresh_ticker.setInterval(int(self._tick_interval * 1000))

    @QtCore.pyqtSlot(int)
    def set_refresh_ticker_rate(self, tps):
        """Set a new refresh rate for the viewport ticker.

        :param tps: Ticks per second.
        :type tps: int
        """
        self._tps = tps
        self._tick_interval = 1.0 / self._tps
        self.refresh_ticker.stop()
        self.refresh_ticker.setInterval(int(self._tick_interval * 1000))
        self.refresh_ticker.start()

    @QtCore.pyqtSlot(float)
    def set_safe_image_grab_coefficient(self, value):
        """Set the safe image grab coefficient.

        A low value will more easily use a previously grabbed frame instead of grabbing the new one.

        :param value: The new value.
        :type value: float
        """
        self._safe_image_grab_coefficient = value

    def get_image(self, in_calibration=False, number_of_squares_w=23, number_of_squares_h=18):
        """Get image from current camera.

        :param in_calibration: Whether or not this frame is for calibration. (False)
        :type in_calibration: bool

        :param number_of_squares_w: The number of squares on the checkerboard's width direction. (23)
        :type number_of_squares_w: int

        :param number_of_squares_h: The number of squares on the checkerboard's height direction. (18)
        :type number_of_squares_h: int

        :return: Image and info string "{width}x{height} @ {fps}fps".
        :rtype: tuple[:class:`QImage`, str]

            .. note:: Image and or info string could be None.
        """
        current_camera = self.camera_manager.get_camera()
        if current_camera is None:
            return None, None

        if self._previous_processing_time >= self._safe_image_grab_coefficient * self._tick_interval:
            self._previous_processing_time -= self._tick_interval
            return self.latest_image, None

        start_process = time.time()

        camera_frame, info_str = current_camera.get_frame(return_info=True)

        # No image in feed, display special message
        if camera_frame is None:
            frame = common.get_frame_with_text("Please wait" + "." * (int(self._animation_frame / 30) % 4))
            image = QtGui.QImage(
                frame,
                frame.shape[1],
                frame.shape[0],
                frame.strides[0],
                QtGui.QImage.Format.Format_BGR888
            )
            self._animation_frame += 1

            return image, info_str

        # Valid image in feed
        else:
            self._animation_frame = 0

            if in_calibration:
                camera_frame = self.camera_calibration_helper.find_chessboard_corners(
                    camera_frame,
                    number_of_squares_w=number_of_squares_w,
                    number_of_squares_h=number_of_squares_h
                )

            elif current_camera.is_calibrated():
                camera_frame = current_camera.undistort(camera_frame)

            self.latest_image = QtGui.QImage(
                camera_frame,
                camera_frame.shape[1],
                camera_frame.shape[0],
                camera_frame.strides[0],
                QtGui.QImage.Format.Format_BGR888
            )

            self._previous_processing_time = time.time() - start_process

            return self.latest_image, info_str

    def stop_all(self):
        """Stop all timers and cameras."""
        self.refresh_ticker.stop()
        self.camera_manager.release_all()
