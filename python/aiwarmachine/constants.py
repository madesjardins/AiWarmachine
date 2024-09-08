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
"""Various constants."""

import os
import sys

from PyQt6 import QtWidgets, QtCore
import cv2 as cv

VERSION = "v0.0.5"  # major.minor.build

GITHUB_WIKI_URL = "https://github.com/madesjardins/AiWarmachine/wiki"

IS_LINUX = sys.platform.startswith('linux')

TEMP_DIRPATH = os.getenv("TEMP_DIRPATH")
VOICE_NARRATOR_TEMP_OUTPUT_FILEPATH_TEMPLATE = os.path.join(TEMP_DIRPATH, "narrator.{:04d}.wav")
PIPER_DIRPATH = os.getenv("PIPER_DIRPATH")
PIPER_EXECUTABLE = os.path.join(PIPER_DIRPATH, "piper.exe")
PIPER_VOICES_DIRPATH = os.path.join(PIPER_DIRPATH, "voices")

CRITERIA = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

DEFAULT_TICKS_PER_SECOND = 30
DEFAULT_PROJECTOR_FRAMES_PER_SECOND = 15
DEFAULT_QR_DETECTION_PER_SECOND = 10

DEFAULT_CAPTURE_API = cv.CAP_V4L2 if IS_LINUX else cv.CAP_DSHOW

DEFAULT_CAPTURE_WIDTH = 1920
DEFAULT_CAPTURE_HEIGHT = 1080
DEFAULT_FPS = 30

DEFAULT_CAPTURE_PROPERTIES_DICT = {
    cv.CAP_PROP_HW_ACCELERATION: cv.VIDEO_ACCELERATION_ANY,
    cv.CAP_PROP_FRAME_WIDTH: DEFAULT_CAPTURE_WIDTH,
    cv.CAP_PROP_FRAME_HEIGHT: DEFAULT_CAPTURE_HEIGHT,
    cv.CAP_PROP_FPS: DEFAULT_FPS,
    cv.CAP_PROP_AUTOFOCUS: 1,  # 1 = Off
    cv.CAP_PROP_FOCUS: 0,  # small = far, big = near
    cv.CAP_PROP_AUTO_EXPOSURE: 1,  # 1 = Off
    cv.CAP_PROP_EXPOSURE: 250 if IS_LINUX else -5,
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

FOURCC_INT_TO_STR = {
    1196444237: 'MJPG',
    825307737: 'Y211',
    825308249: 'Y411',
    844715353: 'YUY2',
    842094169: 'YV12',
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

MAXIMUM_CLOSEST_TABLE_CORNERS_DISTANCE = 15

TABLE_CORNERS_INDEX_BL = 0
TABLE_CORNERS_INDEX_TL = 1
TABLE_CORNERS_INDEX_TR = 2
TABLE_CORNERS_INDEX_BR = 3

TABLE_CORNERS_NAME_TO_INDEX = {
    "bl": TABLE_CORNERS_INDEX_BL,
    "tl": TABLE_CORNERS_INDEX_TL,
    "tr": TABLE_CORNERS_INDEX_TR,
    "br": TABLE_CORNERS_INDEX_BR
}

TABLE_CORNERS_INDEX_TO_COLOR = {
    TABLE_CORNERS_INDEX_BL: QtCore.Qt.GlobalColor.green,
    TABLE_CORNERS_INDEX_TL: QtCore.Qt.GlobalColor.blue,
    TABLE_CORNERS_INDEX_TR: QtCore.Qt.GlobalColor.red,
    TABLE_CORNERS_INDEX_BR: QtCore.Qt.GlobalColor.yellow,
}

TABLE_CORNERS_DRAWING_ORDER = [TABLE_CORNERS_INDEX_BL, TABLE_CORNERS_INDEX_TL, TABLE_CORNERS_INDEX_TR, TABLE_CORNERS_INDEX_BR]

QR_CENTER_EPISLON = 4

TABLE_CORNERS_TYPE_CAMERA = 0
TABLE_CORNERS_TYPE_PROJECTOR = 1
TABLE_CORNERS_TYPE_NAME_TO_INDEX = {
    "camera": TABLE_CORNERS_TYPE_CAMERA,
    "projector": TABLE_CORNERS_TYPE_PROJECTOR
}

TABLE_CORNERS_AXIS_X = 0
TABLE_CORNERS_AXIS_Y = 1
TABLE_CORNERS_AXIS_NAME_TO_INDEX = {
    'x': TABLE_CORNERS_AXIS_X,
    'y': TABLE_CORNERS_AXIS_Y
}

MOVE_KEY_POINTS_DICT = {
    "a": QtCore.QPoint(-1, 0),
    "s": QtCore.QPoint(0, 1),
    "d": QtCore.QPoint(1, 0),
    "w": QtCore.QPoint(0, -1),
}

ROI_MIN_X = 0
ROI_MIN_Y = 1
ROI_MAX_X = 2
ROI_MAX_Y = 3
