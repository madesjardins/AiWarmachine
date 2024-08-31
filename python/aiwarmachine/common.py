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
"""common functions."""

import os
import json

from PyQt6 import QtWidgets, QtGui
import cv2 as cv
import numpy as np

from . import constants


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
    if (icon_obj := constants.MESSAGE_BOX_ICON_NAME_TO_OBJECT_DICT.get(icon_name, None)) is not None:
        msg_dial.setIcon(icon_obj)
    else:
        msg_dial.setIcon(constants.MESSAGE_BOX_ICON_NAME_TO_OBJECT_DICT["NoIcon"])

    valid_button_objs_list = [
        _button_obj
        for _button_name in button_names_list
        if (_button_obj := constants.MESSAGE_BOX_BUTTON_NAME_TO_OBJECT_DICT.get(_button_name, None)) is not None
    ]
    if not valid_button_objs_list:
        valid_button_objs_list = [constants.MESSAGE_BOX_BUTTON_NAME_TO_OBJECT_DICT["Close"]]

    buttons_flag = valid_button_objs_list[0]
    if len(valid_button_objs_list) > 1:
        for button_obj in valid_button_objs_list[1:]:
            buttons_flag = buttons_flag | button_obj

    msg_dial.setStandardButtons(buttons_flag)
    ret_value = find_key_for_value_in_dict(msg_dial.exec(), constants.MESSAGE_BOX_BUTTON_NAME_TO_OBJECT_DICT)
    msg_dial.deleteLater()
    return ret_value


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


def get_capture_property_id(property_name):
    """Get the capture property id from name.

    :param property_name: The name of the property.
    :type property_name: str

    :return: The property id.
    :rtype: int
    """
    return find_key_for_value_in_dict(
        property_name,
        constants.CAPTURE_PROPERTIES_NAMES_DICT
    )


def get_aiwarmachine_root_dir():
    """Get the AiWarmachine root directory.

    :return: The directory path.
    :rtype: str
    """

    return os.path.dirname(os.getenv('AIWARMACHINE_PYTHON_DIR').replace("\\", "/"))


def get_saved_subdir(subdir_name):
    """Get a saved subdirectory path and create it if it does not exist.

    :param subdirectory_name

    :return: The directory path.
    :rtype: str
    """
    subdir_path = f"{get_aiwarmachine_root_dir()}/saved/{subdir_name}"
    if not os.path.exists(subdir_path):
        os.makedirs(subdir_path)
    return subdir_path


def get_color_from_name(color_name, alpha=255):
    """Get a QColor from a color name.

    :param color_name: The color name.
    :type color_name: str

        .. note:: Valid choices are:
            -Black
            -Gray
            -White
            -Yellow
            -Orange
            -Red
            -Magenta
            -Purple
            -Blue
            -Cyan
            -Teal
            -Green
            -Lime

    :param alpha: Alpha value. (255)
    :type alpha: int

    :return: QColor object.
    :rtype: :class:`QColor`

    :raise: ValueError if color is unknown.
    """
    if color_name == "Black":
        return QtGui.QColor(0, 0, 0, alpha)
    elif color_name == "Gray":
        return QtGui.QColor(165, 165, 165, alpha)
    elif color_name == "White":
        return QtGui.QColor(255, 255, 255, alpha)
    elif color_name == "Yellow":
        return QtGui.QColor(255, 241, 0, alpha)
    elif color_name == "Orange":
        return QtGui.QColor(255, 140, 0, alpha)
    elif color_name == "Red":
        return QtGui.QColor(232, 17, 35, alpha)
    elif color_name == "Magenta":
        return QtGui.QColor(236, 0, 140, alpha)
    elif color_name == "Purple":
        return QtGui.QColor(104, 33, 122, alpha)
    elif color_name == "Blue":
        return QtGui.QColor(0, 24, 143, alpha)
    elif color_name == "Cyan":
        return QtGui.QColor(0, 188, 242, alpha)
    elif color_name == "Teal":
        return QtGui.QColor(0, 178, 148, alpha)
    elif color_name == "Green":
        return QtGui.QColor(0, 158, 73, alpha)
    elif color_name == "Lime":
        return QtGui.QColor(186, 216, 10, alpha)

    raise ValueError(f"Color '{color_name}' is unknown.")


def composite_images(
    image_base,
    image_overlay,
    overlay_x=0,
    overlay_y=0,
    image_format=QtGui.QImage.Format.Format_ARGB32_Premultiplied,
    composite_mode=QtGui.QPainter.CompositionMode.CompositionMode_SourceOver,
):
    """Composite 2 images using specific mode.

    :param image_base: The base image.
    :type image_base: :class:`QImage`

    :param image_overlay: The image to composite over the base image.
    :type image_overlay: :class:`QImage`

    :param overlay_x: Horizontal overlay offset in pixels. (0)
    :type overlay_x: int

    :param overlay_y: Vertical overlay offset in pixels. (0)
    :type overlay_y: int

    :param image_format: The returned image format. (QtGui.QImage.Format.Format_ARGB32_Premultiplied)
    :type image_format: :class:`Format`

    :param composite_mode: The composite mode. (QtGui.QPainter.CompositionMode.CompositionMode_SourceOver)
    :type composite_mode: :class:`CompositionMode`

    :return: Composite image.
    :rtype: :class:`QImage`
    """
    image_result = QtGui.QImage(image_base.size(), image_format)
    painter = QtGui.QPainter(image_result)

    painter.setCompositionMode(QtGui.QPainter.CompositionMode.CompositionMode_Source)
    painter.drawImage(0, 0, image_base)

    painter.setCompositionMode(composite_mode)
    painter.drawImage(overlay_x, overlay_y, image_overlay)

    painter.end()

    return image_result


def load_camera_data(filepath):
    """Load camera data from file and format it properly.

    :param filepath: The json filepath.
    :type filepath: str

    :return: Camera data.
    :rtype: dict
    """
    with open(filepath, 'r') as fid:
        camera_data = json.loads(fid.read())

    camera_data['capture_properties_dict'] = {int(_k): _v for _k, _v in camera_data['capture_properties_dict'].items()}
    camera_data['mtx'] = np.array(camera_data['mtx'], np.float32) if camera_data['mtx'] is not None else None
    camera_data['dist'] = np.array(camera_data['dist'], np.float32) if camera_data['dist'] is not None else None
    camera_data['mtx_prime'] = np.array(camera_data['mtx_prime'], np.float32) if camera_data['mtx_prime'] is not None else None
    camera_data['roi'] = np.array(camera_data['roi'], np.int16) if camera_data['roi'] is not None else None
    camera_data['tvec'] = np.array(camera_data['tvec'], np.float32) if camera_data['tvec'] is not None else None
    camera_data['rvec'] = np.array(camera_data['rvec'], np.float32) if camera_data['rvec'] is not None else None

    return camera_data


def convert_qimage_to_numpy_array(image):
    """Convert a QImage to a numpy array.

    :param image: The image to convert.
    :type image: :class:`QImage`

    :return: Numpy image.
    :rtype: :class:`numpy.ndarray`
    """
    width = image.width()
    height = image.height()

    ptr = image.constBits()
    ptr.setsize(height * width * 3)
    arr = np.array(ptr).reshape(height, width, 3)  # Copies the data
    return arr
