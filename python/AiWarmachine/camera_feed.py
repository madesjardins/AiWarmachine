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
"""CameraFeed class module.

A CameraFeed object is what actually grabs the frame from the webcam.
Every valid Camera has a CameraFeed object.
Once you start the CameraFeed, frames will be grabbed and a frame_grabbed signal will be emitted.
Frames sent through the signal are :class:`numpy.ndarray`.
"""
import traceback

import numpy as np
import cv2 as cv
from PyQt6 import QtCore

from . import constants
from . import common


class CameraFeed(QtCore.QThread):
    """CameraFeed grabs frames continuously in a seperate thread once started."""

    # Signal whenever a frame was grabbed.
    # The first argument is the frame and the second,
    # a boolean to specify if the capture was actually successful.
    frame_grabbed = QtCore.pyqtSignal(np.ndarray, bool)

    def __init__(self, camera, capture_api=constants.DEFAULT_CAPTURE_API, debug=False):
        """Initialize.

        :param camera: Camera to initialize the feed from.
        :type camera: :class:`Camera`

        :param capture_api: Preferred Capture API backends to use. (constants.DEFAULT_CAPTURE_API)
        :type capture_api: int

        :param debug: Whether or not to print debug messages. (False)
        :type debug: bool
        """
        super().__init__()

        self._camera = camera
        self._capture_api = capture_api
        self._capture = None
        self._send_signal = False
        self._is_running = False
        self._capture_properties_dict = self._camera.get_capture_properties_copy()
        self.debug = debug

    def _get_capture_resolution(self):
        """Get the current capture width and height.

        This is only used in the case there's a problem with frame grabbing and we want to
        send a red frame. This resolution could differ from the actual one.

        :return: Width and height in pixels based on camera capture properties.
        :rtype: tuple of int
        """
        return (
            self._capture_properties_dict.get(cv.CAP_PROP_FRAME_WIDTH, constants.DEFAULT_CAPTURE_WIDTH),
            self._capture_properties_dict.get(cv.CAP_PROP_FRAME_HEIGHT, constants.DEFAULT_CAPTURE_HEIGHT)
        )

    def _update_capture_if_needed(self):
        """Update current VideoCapture and capture properties with new ones from the camera if needed.

        :param capture_properties_dict: The new properties to use.
        :type capture_properties_dict: dict

        :return: Whether or not an update was required.
        :rtype: bool
        """
        required_update = False
        if self._capture is not None and self._capture.isOpened():
            camera_capture_properties_dict = self._camera.get_capture_properties_copy()
            for property_id, new_value in camera_capture_properties_dict.items():
                if new_value != self._capture_properties_dict.get(property_id):
                    if self.debug:
                        property_name = constants.CAPTURE_PROPERTIES_NAMES_DICT.get(property_id, 'Unknown')
                        print(f"Updating capture property '{property_name}' with value {new_value}. [{self._capture.set(property_id, new_value)}]")
                    required_update = True

            if required_update:
                self._capture_properties_dict = camera_capture_properties_dict

        return required_update

    def stop(self):
        """Stop the frame grab only.

        When calling this method, you should also call wait() to make sure it stopped.
        """
        self._send_signal = False
        self._is_running = False

    def release(self):
        """Stop frame grab and release video capture device.

        When calling this method, you should also call wait() to make sure it stopped.
        """
        self.stop()
        if self._capture and self._capture.isOpened():
            self._capture.release()
        self._capture = None

    def run(self):
        """Start grabbing frames from device and emit signal with each frame.

        :raise: :class:`IOError` if unable to create VideoCapture object.
        :emit: frame_grabbed signal for each frame.
        """
        self.stop()

        # Open video capture for device
        if self._capture is None or not self._capture.isOpened():
            props_list = []
            for property_value in self._capture_properties_dict.items():
                props_list.extend(property_value)
            if self.debug:
                print(f"Creating VideoCapture for '{self._camera.name}' device ID {self._camera.device_id}.")
                print(f"Using properties: {props_list}.")
            try:
                self._capture = cv.VideoCapture(
                    self._camera.device_id,
                    constants.DEFAULT_CAPTURE_API,
                    props_list
                )
            except Exception:
                print(f"ERROR: Unable create VideoCapture '{self._camera.name}'.")
                traceback.print_exc()
                frame = common.get_frame_with_text("Failed to create VideoCapture.", fontsize=2)
                self.frame_grabbed.emit(frame, False)
                return

            if self._capture is None or not self._capture.isOpened():
                print(f"ERROR: Unable to start camera feed for camera '{self._camera.name}'.")
                frame = common.get_frame_with_text("Unable to start camera feed.", fontsize=2)
                self.frame_grabbed.emit(frame, False)
                return

        self._send_signal = True
        self._is_running = True
        while self._capture is not None and self._capture.isOpened() and self._is_running:

            self._update_capture_if_needed()

            try:
                cap_ret, frame = self._capture.read()
            except Exception:
                cap_ret = None

            if not cap_ret:
                # Problem while reading, put red frame in BGR888 format
                width, height = self._get_capture_resolution()
                frame = np.zeros(
                    (
                        height,
                        width,
                        3
                    ),
                    dtype=np.uint8
                )
                frame[:, :] = (0, 0, 255)

            if self._send_signal:
                self.frame_grabbed.emit(frame, cap_ret)
