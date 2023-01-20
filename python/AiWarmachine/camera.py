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
"""Camera Class.

Once the Camera is initialized, simply call start() to start its CameraFeed.
You can then call get_frame() to get the latest frame available.
"""

import copy
import time

from PyQt6 import QtCore
import numpy as np
import cv2 as cv

from . import constants
from . import camera_feed


class Camera(QtCore.QObject):
    """A camera class with calibration capabilities."""

    def __init__(
        self,
        name="",
        model_name="",
        device_id=0,
        capture_properties_dict=None,
        int_mat=None,
        dist_coeffs=None,
        tvec=None,
        rvec=None,
        debug=False
    ):
        """Initialize.

        :param name: A name to describe the camera.
        :type name: str

            **Example: 'Top View'**

        :param model_name: The camera model name.
        :type model_name: str

            **Example: 'Logitech HD Pro Webcam C920'**

        :param device_id: The capture device ID. (0)
        :type device_id: int

        :param capture_properties_dict: The capture properties dictionary. (None)
        :type capture_properties_dict: int

        :param int_mat: Intrinsic camera matrix. (None)
        :type int_mat: Numpy array 3x3

        :param dist_coeffs: Distortion Coefficients. (None)
        :type dist_coeffs: Numpy array 1xX

        :param tvec: Translation vector. (None)
        :type tvec: Numpy array 1x3

        :param rvec: Rodrigues rotation vector. (None)
        :type rvec: Numpy Array 1x3

        :param debug: Whether or not to print debug messages. (False)
        :type debug: bool
        """
        super().__init__()

        # basic info
        self.name = name
        self.model_name = model_name
        self.debug = debug

        # calibration params
        self._int_mat = int_mat
        self._dist_coeffs = dist_coeffs
        self._tvec = tvec
        self._rvec = rvec

        # camera feed
        self._device_id = device_id
        if capture_properties_dict is None:
            capture_properties_dict = copy.deepcopy(constants.DEFAULT_CAPTURE_PROPERTIES_DICT)
        self._capture_properties_dict = capture_properties_dict
        self._camera_feed = camera_feed.CameraFeed(self, debug=self.debug)
        self._camera_feed.frame_grabbed.connect(self.new_frame)

        # frame buffer
        self._reset_framebuffer()

        self._previous_time = time.time()
        self.current_fps = 0.0

        self._effective_resolution = [None, None]

    def _reset_framebuffer(self):
        """Reset the framebuffer and framebuffer index."""
        self._framebuffer_list = [None, None, None]
        self._framebuffer_index = -1

    def start(self):
        """Start the camera feed."""
        self._previous_time = time.time()
        self._camera_feed.start()

    def stop(self):
        """Stop the camera feed without destroying it."""
        self._camera_feed.stop()
        self._camera_feed.wait()

    def release(self):
        """Stop and release the camera feed if any."""
        self._camera_feed.release()
        self._camera_feed.wait()

    @QtCore.pyqtSlot(np.ndarray, bool)
    def new_frame(self, frame, valid_frame):
        """Frame received from camera feed.

        :param frame: The frame.
        :type frame: :class:`numpy.ndarray`

        :param valid_frame: Whether or not this frame is valid.
        :type valid_frame: bool
        """
        time_delay = time.time() - self._previous_time
        self.current_fps = 1.0 / max(0.0001, time_delay)

        buffer_id = (self._framebuffer_index + 1) % 3
        self._framebuffer_list[buffer_id] = frame
        self._framebuffer_index = buffer_id

        self._previous_time = time.time()
        if valid_frame:
            # update actual capture resolution
            self._effective_resolution = [frame.shape[1], frame.shape[0]]

    def get_frame(self, show_info=False, return_info=False):
        """Get the latest frame available.

        :param show_info: Print resolution and fps on the image. (False)
        :type show_info: bool

        :param return_info: If set to True, will also return info string "{width}x{height} @ {fps}fps" along with the frame as a tuple. (False)
        :type return_info: bool

        :return: The frame.
        :rtype: :class:`numpy.ndarray`
        """
        if self._framebuffer_index >= 0:
            frame = self._framebuffer_list[self._framebuffer_index]
            info_str = f'{frame.shape[1]}x{frame.shape[0]} @ {self.current_fps:0.1f}fps'
            if show_info:
                info_frame = cv.putText(
                    frame,
                    info_str,
                    (50, 50),
                    cv.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 255, 255),
                    2,
                    cv.LINE_AA
                )
                if return_info:
                    return info_frame, info_str
                else:
                    return info_frame,

            elif return_info:
                return frame, info_str

            else:
                return frame

        else:
            return None

    @property
    def device_id(self):
        """Get this camera device id.

        :return: Device ID
        :rtype: int
        """
        return self._device_id

    @device_id.setter
    def device_id(self, device_id):
        """Set the camera new device id.

        If the feed was running, restart the feed.

        :param device_id: The device id.
        :type device_id: int
        """
        feed_was_running = self._camera_feed.isRunning()
        self.release()
        self._device_id = device_id
        self._reset_framebuffer()
        if feed_was_running:
            self.start()

    def get_capture_properties_copy(self):
        """Get a copy of this camera capture properties.

        :return: Capture properties.
        :rtype: dict
        """
        return copy.deepcopy(self._capture_properties_dict)

    def set_capture_property(self, property_id, value):
        """Set a capture property.

        :param property_id: cv.VideoCaptureProperties enum value.
        :type property_id: int

        :param value: Value.
        :type value: any
        """
        self._capture_properties_dict[property_id] = value

    def get_capture_property(self, property_id):
        """Get a capture property.

        :param property_id: cv.VideoCaptureProperties enum value.
        :type property_id: int

        :return: Value of the property.
        :rtype: any
        """
        return self._capture_properties_dict.get(property_id)

    def is_running(self):
        """Whether or not the feed is running.

        :return: Whether or not the feed is running.
        :rtype: bool
        """
        return self._camera_feed.isRunning()
