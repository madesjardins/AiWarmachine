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
import json
import re

from PyQt6 import QtCore
import numpy as np
import cv2 as cv

from . import constants
from . import camera_feed
from . import common


class Camera(QtCore.QObject):
    """A camera class with calibration capabilities."""

    def __init__(
        self,
        name="",
        model_name="",
        device_id=0,
        capture_properties_dict=None,
        mtx=None,
        dist=None,
        mtx_prime=None,
        roi=None,
        tvec=None,
        rvec=None,
        table_offset_tvec=None,
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

        :param mtx: Intrinsic camera 3x3 matrix. (None)
        :type mtx: :class:`numpy.ndarray`

        :param dist: Distortion Coefficients. (None)
        :type dist: :class:`numpy.ndarray`

        :param mtx_prime: Optimal new intrinsic camera 3x3 matrix. (None)
        :type mtx_prime: :class:`numpy.ndarray`

        :param roi: Region of interest when using undistorted image and prime matrix. (None)
        :type roi: tuple of int

        :param tvec: Translation vector. (None)
        :type tvec: :class:`ndarray`

        :param rvec: Rodrigues rotation vector. (None)
        :type rvec: :class:`ndarray`

        :param

        :param debug: Whether or not to print debug messages. (False)
        :type debug: bool
        """
        super().__init__()

        # basic info
        self.name = name
        self.model_name = model_name
        self.debug = debug

        # calibration params
        self._mtx = mtx
        self._dist = dist
        self._mtx_prime = mtx_prime
        self._roi = roi
        self._tvec = tvec
        self._rvec = rvec
        self._table_offset_tvec = table_offset_tvec
        if self._table_offset_tvec is None:
            self._table_offset_tvec = np.array([[0], [0], [0]], np.float32)

        # camera feed
        self._device_id = device_id
        if capture_properties_dict is None:
            capture_properties_dict = copy.deepcopy(constants.DEFAULT_CAPTURE_PROPERTIES_DICT)
        self._capture_properties_dict = capture_properties_dict
        self._camera_feed = camera_feed.CameraFeed(self, debug=self.debug)
        self._camera_feed.frame_grabbed.connect(self.new_frame)

        if self._mtx is not None and self._mtx_prime is not None and self._roi is not None:
            image_resolution = (
                self._capture_properties_dict.get(common.get_capture_property_id("Width"), constants.DEFAULT_CAPTURE_WIDTH),
                self._capture_properties_dict.get(common.get_capture_property_id("Height"), constants.DEFAULT_CAPTURE_HEIGHT)
            )
            self._mapx, self._mapy = cv.initUndistortRectifyMap(self._mtx, self._dist, None, self._mtx_prime, image_resolution, 5)
        else:
            self._mapx = None
            self._mapy = None

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
                    return info_frame

            elif return_info:
                return frame, info_str

            else:
                return frame

        elif return_info:
            return None, None

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

    def is_calibrated(self):
        """Whether the camera is calibrated or not.

        :return: True if camera is calibrated.
        :rtype: bool
        """
        return (
            self._mtx is not None and
            self._dist is not None and
            self._mtx_prime is not None and
            self._roi is not None and
            self._mapx is not None and
            self._mapy is not None
        )

    def is_posed(self):
        """Whether the camera is calibrated and posed.

        :return: True if camera is calibrated and posed.
        :rtype: bool
        """
        return (
            self.is_calibrated and
            self._rvec is not None and
            self._tvec is not None and
            self._table_offset_tvec is not None
        )

    def calibrate(self, checkerboard_3d_points_3_list, checkerboard_2d_points_3_list, image_resolution):
        """Calculate and set camera matrix, ROI and mapping function to undistort images.

        :param checkerboard_3d_points_3_list: Three lists (one for each calibration view) of array of 3d points.
        :type checkerboard_3d_points_3_list: list of :class:`numpy.ndarray`

        :param checkerboard_2d_points_3_list: Three lists (one for each calibration view) of array of corresponding 2d points.
        :type checkerboard_2d_points_3_list: list of :class:`numpy.ndarray`

        :param image_resolution: The image resolution as (width, height).
        :type image_resolution: tupple of int

        :return: Mean reprojection error.
        :rtype: float
        """
        ret, mtx, dist, rvecs_list, tvecs_list = cv.calibrateCamera(
            checkerboard_3d_points_3_list,
            checkerboard_2d_points_3_list,
            image_resolution,
            None,
            None
        )

        if not ret:
            raise RuntimeError("Unable to calibrate camera with these images.")

        self._mtx = mtx
        self._dist = dist
        self._mtx_prime, self._roi = cv.getOptimalNewCameraMatrix(self._mtx, self._dist, image_resolution, 1, image_resolution)
        self._mapx, self._mapy = cv.initUndistortRectifyMap(self._mtx, self._dist, None, self._mtx_prime, image_resolution, 5)
        mean_error = 0
        for i in range(len(checkerboard_3d_points_3_list)):
            projected_2d_points_array, _ = cv.projectPoints(checkerboard_3d_points_3_list[i], rvecs_list[i], tvecs_list[i], mtx, dist)
            error = cv.norm(checkerboard_2d_points_3_list[i], projected_2d_points_array, cv.NORM_L2) / len(projected_2d_points_array)
            mean_error += error

        return mean_error / len(checkerboard_3d_points_3_list)

    def undistort(self, frame):
        """Undistort image.

        :param frame: The image.
        :type frame: :class:`numpy.ndarray`
        """
        dst = cv.remap(frame, self._mapx, self._mapy, cv.INTER_CUBIC)
        x, y, w, h = self._roi
        return dst[y:y + h, x:x + w].copy()

    def pose(self, checkerboard_3d_points_list, checkerboard_2d_points_list):
        """Calculate the pose of the camera for a frame.

        :param checkerboard_3d_points_3_list: Array of 3d points.
        :type checkerboard_3d_points_3_list: :class:`numpy.ndarray`

        :param checkerboard_2d_points_3_list: Array of corresponding 2d points.
        :type checkerboard_2d_points_3_list: :class:`numpy.ndarray`
        """
        ret, rvec, tvec = cv.solvePnP(
            checkerboard_3d_points_list,
            checkerboard_2d_points_list,
            self._mtx,
            self._dist
        )
        if not ret:
            raise RuntimeError("Unable to determine camera pose.")

        self._rvec = rvec
        self._tvec = tvec

        print(f"Translation : {list(self._tvec)}\nRotation : {list(self._rvec)}")

    def project_points(self, points_array, undistorted=False, as_integers=False):
        """Project 3d points into 2d image space.

        :param points_array: Array of 3d points.
        :type points_array: :class:`numpy.ndarray`

        :param undistorted: Whether or not to return 2d coordinates of the undistorted image. (False)
        :type undistorted: bool

        :param as_integers: Whether or not to convert to int instead of float. (False)
        :type as_integers: bool
        """
        tvec = self._tvec - self._table_offset_tvec
        projected_2d_points_array, _ = cv.projectPoints(
            points_array,
            self._rvec,
            tvec,
            self._mtx_prime if undistorted else self._mtx,
            self._dist
        )

        if undistorted:
            x, y, _, _ = self._roi
            for index in range(len(projected_2d_points_array)):
                projected_2d_points_array[index][0][0] -= x
                projected_2d_points_array[index][0][1] -= y

        if as_integers:
            return (np.rint(projected_2d_points_array)).astype(int)
        else:
            return projected_2d_points_array

    def set_table_offset(self, x, y, z):
        """Set the table offset translation vector.

        :param x: X.
        :type x: float

        :param y: Y.
        :type y: float

        :param z: Z.
        :type z: float
        """
        self._table_offset_tvec = np.array([[x], [y], [z]], np.float32)

    def save(self):
        """Save the current camera settings and calibration.

        :return: Filepath.
        :rtype: str

        :raise: RuntimeError if camera does not have a name.
        """
        if not self.name:
            raise RuntimeError("Camera does not have a name.")

        capture_properties_dict = self.get_capture_properties_copy()
        capture_width = capture_properties_dict.get(common.get_capture_property_id("Width"))
        capture_height = capture_properties_dict.get(common.get_capture_property_id("Height"))
        capture_zoom = capture_properties_dict.get(common.get_capture_property_id("Zoom"))
        capture_focus = capture_properties_dict.get(common.get_capture_property_id("Focus"))

        calibration_dir = common.get_calibration_dir()
        name = re.sub('[^a-zA-Z0-9]', '_', self.name)
        calibration_filename = f"{name}__{capture_width}x{capture_height}__z{capture_zoom}__f{capture_focus}.json"
        calibration_filepath = f"{calibration_dir}/{calibration_filename}"

        data = {
            'name': self.name,
            'device_id': self.device_id,
            'model_name': self.model_name,
            'capture_properties_dict': capture_properties_dict,
            'mtx': self._mtx.tolist() if self._mtx is not None else None,
            'dist': self._dist.tolist() if self._dist is not None else None,
            'mtx_prime': self._mtx_prime.tolist() if self._mtx_prime is not None else None,
            'roi': self._roi,
            'tvec': self._tvec.tolist() if self._tvec is not None else None,
            'rvec': self._rvec.tolist() if self._rvec is not None else None,
            'table_offset_tvec': self._table_offset_tvec.tolist() if self._table_offset_tvec is not None else None,

        }
        with open(calibration_filepath, 'w') as fid:
            fid.write(json.dumps(data, indent=2))

        return calibration_filepath
