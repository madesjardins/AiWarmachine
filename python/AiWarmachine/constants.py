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

import cv2 as cv

CRITERIA = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

DEFAULT_CAPTURE_API = cv.CAP_DSHOW

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
    cv.CAP_PROP_EXPOSURE: -6,
    cv.CAP_PROP_FOURCC: cv.VideoWriter_fourcc(*'MJPG'),
}

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
}


CALIBRATION_VIEWS = [
    "Close up from top.",
    "Tilt down from front.",
    "Tilt down from side."
]
