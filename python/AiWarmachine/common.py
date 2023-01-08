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
"""common functions."""

import cv2 as cv
import numpy as np


def cmToIn(value):
    """Convert centimeters value to inches.

    :param value: Value in centimeters.
    :type value: float

    :return: Value in inches.
    :rtype: float
    """
    return value * 0.3937007874015748


def inToCm(value):
    """Convert inches to centimeters.

    :param value: Value in inches.
    :type value: float

    :return: Value in centimeters.
    :rtype: float
    """
    return value * 2.54


def get_frame_with_text(
    text,
    width=960,
    height=540,
    position=None,
    font=cv.FONT_HERSHEY_PLAIN,
    fontsize=8,
    color=None,
    bg_color=None
):
    """Get a frame with text in BGR888 format.

    :param text: The text to write.
    :type text: str

    :param width: The width of the image. (960)
    :type width: int

    :param height: The width of the image. (540)
    :type height: int

    :param position: The text lower left corner position. ((10, height / 2))
    :type position: tuple (int, int)

    :param font: OpenCV font. (cv.FONT_HERSHEY_PLAIN)
    :type font: int

    :param fontsize: The fontsize. (8)
    :type fontsize: int

    :param color: The BGR text color. ((255, 255, 255))
    :type color: tuple (int, int, int)

    :param bg_color: The BGR background color. ((0, 0, 0))
    :type bg_color: tuple (int, int, int)

    :return: A frame with text in BGR888 format.
    :rtype: :class:`numpy.ndarray`
    """
    if position is None:
        position = (10, int(height / 2))
    if color is None:
        color = (255, 255, 255)
    if bg_color is None:
        bg_color = (0, 0, 0)
    frame = np.zeros(
        (
            height,
            width,
            3
        ),
        dtype=np.uint8
    )
    frame[:, :] = bg_color
    return cv.putText(frame, text, position, font, fontsize, color=color, thickness=2, lineType=cv.LINE_AA)
