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
"""Various constants."""

import sys

from PyQt6 import QtWidgets
import cv2 as cv

IS_LINUX = sys.platform.startswith('linux')

CRITERIA = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

DEFAULT_CAPTURE_API = cv.CAP_V4L2 if IS_LINUX else cv.CAP_DSHOW

DEFAULT_CAPTURE_WIDTH = 1920
DEFAULT_CAPTURE_HEIGHT = 1080
DEFAULT_FPS = 30.0

DEFAULT_CAPTURE_PROPERTIES_DICT = {
    cv.CAP_PROP_HW_ACCELERATION: cv.VIDEO_ACCELERATION_ANY,
    cv.CAP_PROP_FRAME_WIDTH: DEFAULT_CAPTURE_WIDTH,
    cv.CAP_PROP_FRAME_HEIGHT: DEFAULT_CAPTURE_HEIGHT,
    cv.CAP_PROP_FPS: int(DEFAULT_FPS),
    cv.CAP_PROP_AUTOFOCUS: 1,  # 1 = Off
    cv.CAP_PROP_FOCUS: 0,  # small = far, big = near
    cv.CAP_PROP_AUTO_EXPOSURE: 1,  # 1 = Off
    cv.CAP_PROP_EXPOSURE: 250 if IS_LINUX else -6,
    cv.CAP_PROP_FOURCC: cv.VideoWriter_fourcc(*'YUY2'),  # MJPG
    cv.CAP_PROP_BRIGHTNESS: 128,
    cv.CAP_PROP_CONTRAST: 128,
    cv.CAP_PROP_GAIN: 128,
    cv.CAP_PROP_SATURATION: 128,
    cv.CAP_PROP_SHARPNESS: 128,
    cv.CAP_PROP_ZOOM: 100,
}
if IS_LINUX:
    # V4L2 does not have focus implemented
    del DEFAULT_CAPTURE_PROPERTIES_DICT[cv.CAP_PROP_FOCUS]

CAPTURE_PROPERTIES_NAMES_DICT = {
    cv.CAP_PROP_HW_ACCELERATION: "Hardware acceleration",
    cv.CAP_PROP_FRAME_WIDTH: "Width",
    cv.CAP_PROP_FRAME_HEIGHT: "Height",
    cv.CAP_PROP_FPS: "FPS",
    cv.CAP_PROP_AUTOFOCUS: "Auto focus",
    cv.CAP_PROP_FOCUS: "Focus",
    cv.CAP_PROP_AUTO_EXPOSURE: "Auto exposure",
    cv.CAP_PROP_EXPOSURE: "Exposure",
    cv.CAP_PROP_FOURCC: "FOURCC",
    cv.CAP_PROP_BRIGHTNESS: "Brightness",
    cv.CAP_PROP_CONTRAST: "Contrast",
    cv.CAP_PROP_GAIN: "Gain",
    cv.CAP_PROP_SATURATION: "Saturation",
    cv.CAP_PROP_SHARPNESS: "Sharpness",
    cv.CAP_PROP_ZOOM: "Zoom",
}


CALIBRATION_VIEWS = [
    "Close up from top.",
    "Tilt down from front.",
    "Tilt down from side."
]

DEFAULT_DEVICE_IDS_LIST = [0, 1, 2, 3, 4]

MESSAGE_BOX_BUTTON_NAME_TO_OBJECT_DICT = {
    "Ok": QtWidgets.QMessageBox.StandardButton.Ok,
    "Open": QtWidgets.QMessageBox.StandardButton.Open,
    "Save": QtWidgets.QMessageBox.StandardButton.Save,
    "Cancel": QtWidgets.QMessageBox.StandardButton.Cancel,
    "Close": QtWidgets.QMessageBox.StandardButton.Close,
    "Yes": QtWidgets.QMessageBox.StandardButton.Yes,
    "No": QtWidgets.QMessageBox.StandardButton.No,
    "Abort": QtWidgets.QMessageBox.StandardButton.Abort,
    "Retry": QtWidgets.QMessageBox.StandardButton.Retry,
    "Ignore": QtWidgets.QMessageBox.StandardButton.Ignore
}

MESSAGE_BOX_ICON_NAME_TO_OBJECT_DICT = {
    "NoIcon": QtWidgets.QMessageBox.Icon.NoIcon,
    "Question": QtWidgets.QMessageBox.Icon.Question,
    "Information": QtWidgets.QMessageBox.Icon.Information,
    "Warning": QtWidgets.QMessageBox.Icon.Warning,
    "Critical": QtWidgets.QMessageBox.Icon.Critical
}

INTERPOLATION_METHOD_NAME_DICT = {
    'Nearest': cv.INTER_NEAREST,
    'Linear': cv.INTER_LINEAR,
    'Cubic': cv.INTER_CUBIC,
    'Lanczos4': cv.INTER_LANCZOS4,
}
