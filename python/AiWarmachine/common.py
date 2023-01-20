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

from PyQt6 import QtWidgets
import cv2 as cv
import numpy as np

from . import constants as aiw_constants


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


def message_box(
    title,
    text,
    info_text=None,
    details_text=None,
    icon_name="NoIcon",
    button_names_list=None
):
    """Pop a message box and wait for user answer.

    :param title: The window title.
    :type title: str

    :param text: Primary text to show.
    :type text: str

    :param info_text: Additional text to show if any. (None)
    :type info_text: str

    :param details_text: Details text to show in a separate section if any. (None)
    :type details_text: str

    :param icon_name: Name of the icon. ("NoIcon")
    :type icon_name: str

        .. note:: The choices of icon name are "Question", "Information", "Warning", "Critical" and "NoIcon".

    :param button_names_list: List of button names to show. (["Close"])
    :type button_names_list: list of str

        .. note:: The choices of button names are "Ok", "Open", "Save", "Cancel", "Close", "Yes", "No", "Abort", "Retry" and "Ignore".

    :return: The name of the pressed button.
    :rtype: str
    """
    msg_dial = QtWidgets.QMessageBox()
    msg_dial.setWindowTitle(title)
    msg_dial.setText(text)
    if info_text:
        msg_dial.setInformativeText(info_text)
    if details_text:
        msg_dial.setDetailedText(details_text)
    if (icon_obj := aiw_constants.MESSAGE_BOX_ICON_NAME_TO_OBJECT_DICT.get(icon_name, None)) is not None:
        msg_dial.setIcon(icon_obj)
    else:
        msg_dial.setIcon(aiw_constants.MESSAGE_BOX_ICON_NAME_TO_OBJECT_DICT["NoIcon"])

    valid_button_objs_list = [
        _button_obj
        for _button_name in button_names_list
        if (_button_obj := aiw_constants.MESSAGE_BOX_BUTTON_NAME_TO_OBJECT_DICT.get(_button_name, None)) is not None
    ]
    if not valid_button_objs_list:
        valid_button_objs_list = [aiw_constants.MESSAGE_BOX_BUTTON_NAME_TO_OBJECT_DICT["Close"]]

    buttons_flag = valid_button_objs_list[0]
    if len(valid_button_objs_list) > 1:
        for button_obj in valid_button_objs_list[1:]:
            buttons_flag = buttons_flag | button_obj

    msg_dial.setStandardButtons(buttons_flag)

    return find_key_for_value_in_dict(msg_dial.exec(), aiw_constants.MESSAGE_BOX_BUTTON_NAME_TO_OBJECT_DICT)


def find_key_for_value_in_dict(value, dictionary, default=None):
    """Find key corresponding value in dictionary.

    :param value: The value you are looking for.
    :type value: object

    :param dictionary: The dict to look into.
    :type dictionary: dict

    :param default: The key to return if value is not found. (None)
    :type default: object

    :return: The key.
    :rtype: object
    """
    for k, v in dictionary.items():
        if v == value:
            return k
    return default
