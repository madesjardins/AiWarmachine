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
"""Module to help calibrate a camera."""

from PyQt6 import QtCore, QtGui
import cv2 as cv
import numpy as np

from . import constants


class CameraCalibrationHelper(QtCore.QObject):
    """Helper class for camera calibration."""

    def __init__(self):
        """Initialize."""
        super().__init__()

        self._calibration_packages_dict = {
            'top': None,
            'front': None,
            'side': None,
        }

        self._last_valid_calibration_pkg = None

    def get_view_names(self):
        """Get all the view names.

        :return: View names.
        :rtype: list[str]
        """
        return list(self._calibration_packages_dict.keys())

    def set_package(self, view_name, package=None, force=False):
        """Set an image and corners package for a view.

        :param view_name: The name of the view in ['top', 'front', 'side'].
        :type view_name: str

        :param package: Package to set on the view as a tuple of image and corners, or None to set latest valid calibration package.
        :type package: tuple[:class:`numpy.ndarray`, :class:`MatLike`]

        :param force: Will set package even if None. (False)
        :type force: bool

        :return: Whether or not a valid package was set.
        :rtype: bool
        """
        is_valid = package is not None

        if force or is_valid:
            self._calibration_packages_dict[view_name] = package
        else:
            is_valid = self._last_valid_calibration_pkg is not None
            self._calibration_packages_dict[view_name] = self._last_valid_calibration_pkg
            self._last_valid_calibration_pkg = None

        return is_valid

    def get_package_image(self, view_name, as_qimage=True, qimage_format=QtGui.QImage.Format.Format_BGR888):
        """Get the image contain in a view package.

        :param view_name: The name of the view in ['top', 'front', 'side'].
        :type view_name: str

        :param as_qimage: If set to True, will return an QImage instead of the ndarray frame. (True)
        :type as_qimage: bool

        :param qimage_format: The returned qimage format. (QtGui.QImage.Format.Format_BGR888)
        :type qimage_format: :class:`Format`

        :return: The grayscale image used for calibration.
        :rtype: :class:`numpy.ndarray`
        """
        frame_gray, _ = self._calibration_packages_dict[view_name]
        if as_qimage:
            frame = cv.cvtColor(frame_gray, cv.COLOR_GRAY2BGR)
            return QtGui.QImage(
                frame,
                frame.shape[1],
                frame.shape[0],
                frame.strides[0],
                qimage_format
            )
        else:
            return frame_gray

    def get_checkerboard_3d_reference_points(self, number_of_squares_w, number_of_squares_h):
        """Get checkboard 3D reference points.

        :param number_of_squares_w: The number of squares on the checkerboard's width direction.
        :type number_of_squares_w: int

        :param number_of_squares_h: The number of squares on the checkerboard's height direction.
        :type number_of_squares_h: int

        :return: Array of reference points.
        :rtype: :class:`np.ndarray`
        """
        dim_x = number_of_squares_w - 1
        dim_x_2 = int(dim_x / 2)
        dim_y = number_of_squares_h - 1
        dim_y_2 = int(dim_y / 2)

        checkerboard_ref_points = []

        for y in range(dim_y - 1, -1, -1):
            for x in range(dim_x):
                checkerboard_ref_points.append([
                    (x - dim_x_2),
                    (y - dim_y_2),
                    0.0
                ])

        return np.array(checkerboard_ref_points, np.float32)

    def calibrate(self, camera, number_of_squares_w, number_of_squares_h):
        """Calibrate the camera using a checkerboard.

        :param camera: The camera to calibrate.
        :type camera: :class:`Camera`

        :param number_of_squares_w: The number of squares on the checkerboard's width direction.
        :type number_of_squares_w: int

        :param number_of_squares_h: The number of squares on the checkerboard's height direction.
        :type number_of_squares_h: int

        :return: The mean error of the calibration.
        :rtype: float
        """
        checkerboard_3d_reference_points_array = self.get_checkerboard_3d_reference_points(
            number_of_squares_w,
            number_of_squares_h
        )
        checkerboard_3d_points_list = []
        checkerboard_2d_points_list = []
        image_resolution = None
        for frame_gray, corners in self._calibration_packages_dict.values():
            image_resolution = frame_gray.shape[::-1]
            corners2 = cv.cornerSubPix(
                frame_gray,
                corners,
                (11, 11),
                (-1, -1),
                constants.CRITERIA
            )

            checkerboard_3d_points_list.append(checkerboard_3d_reference_points_array)
            checkerboard_2d_points_list.append(corners2)

        return camera.calibrate(
            checkerboard_3d_points_list,
            checkerboard_2d_points_list,
            image_resolution
        )

    def uncalibrate(self, camera):
        """Uncalibrate a camera.

        :param camera: The camera to uncalibrate.
        :type camera: :class:`Camera`
        """
        camera.uncalibrate()
        for view_name in self._calibration_packages_dict.keys():
            self._calibration_packages_dict[view_name] = None

    def find_chessboard_corners(self, camera_frame, number_of_squares_w, number_of_squares_h, draw_corners=True):
        """Find the chessboard corners in the image and store package internally if valid.

        :param camera: The camera to calibrate.
        :type camera: :class:`Camera`

        :param number_of_squares_w: The number of squares on the checkerboard's width direction.
        :type number_of_squares_w: int

        :param number_of_squares_h: The number of squares on the checkerboard's height direction.
        :type number_of_squares_h: int

        :param draw_corners: Whether to draw the corners or not on the returned image. (True)
        :type draw_corners: bool

        :return: The image.
        :rtype: :class:`numpy.ndarray`
        """
        gray = cv.cvtColor(camera_frame, cv.COLOR_BGR2GRAY)

        checkerboard_dim = (
            number_of_squares_w - 1,
            number_of_squares_h - 1
        )
        ret, corners = cv.findChessboardCorners(gray, checkerboard_dim, flags=cv.CALIB_CB_FAST_CHECK)
        if ret:
            self._last_valid_calibration_pkg = gray, corners
            if draw_corners:
                camera_frame = cv.drawChessboardCorners(
                    cv.cvtColor(gray, cv.COLOR_GRAY2BGR),
                    checkerboard_dim,
                    corners,
                    ret
                )
        return camera_frame

    def has_all_calibration_images(self):
        """Get whether or not all calibration images are there.

        :return: True if all calibration images are present.
        :rtype: bool
        """
        return sum([1 for _view_image in self._calibration_packages_dict.values() if _view_image is not None]) == len(self._calibration_packages_dict)