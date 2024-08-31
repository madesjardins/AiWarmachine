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
"""Camera manager modules for camera related operations."""

from PyQt6 import QtCore
import cv2 as cv

from . import constants, camera


class CameraManager(QtCore.QObject):
    """Manages all camera related operations."""

    def __init__(self):
        """Initialize."""
        super().__init__()

        self._cameras_dict = {}
        self._current_camera_id = -1

    def get_available_device_ids_list(self, as_list_of_str=False):
        """Get the available device ids list.

        :param as_list_of_str: If set to True, will return a list of str instead of int. (False)
        :type as_list_of_str: bool

        :return: Device ids not taken yet.
        :rtype: list of int
        """
        cast_class = int
        if as_list_of_str:
            cast_class = str
        return [cast_class(_i) for _i in constants.DEFAULT_DEVICE_IDS_LIST if _i not in self._cameras_dict]

    def add_camera(self, **kwargs):
        """Add a new camera to the list, see camera.Camera for all available kwargs.

        :return: The newly added camera.
        :rtype: :class:`Camera`
        """
        device_id = kwargs.get('device_id', 0)
        new_camera_obj = camera.Camera(**kwargs)
        self._cameras_dict[device_id] = new_camera_obj
        self._current_camera_id = device_id
        return new_camera_obj

    def get_camera(self, device_id=None):
        """Get the current camera or a camera with a specific device id.

        :param device_id: The capture device ID, or the current camera if None. (None)
        :type device_id: int

        :return: Camera.
        :rtype: :class:`Camera`
        """
        if device_id is None:
            device_id = self._current_camera_id
        return self._cameras_dict.get(device_id)

    def set_current_camera(self, device_id):
        """Set the camera with specific device id as current.

        param device_id: The capture device ID.
        :type device_id: int

        :return: Whether or not this operation was possible.
        :rtype: bool
        """
        if (camera_obj := self.get_camera(device_id)) is not None:
            if not camera_obj.is_running():
                camera_obj.start()
            self._current_camera_id = device_id
            return True
        else:
            return False

    def delete_camera(self, device_id):
        """Remove a camera from the lot.

        param device_id: The capture device ID.
        :type device_id: int

        :return: Whether or not this operation was possible.
        :rtype: bool
        """
        if (camera_obj := self.get_camera(device_id)) is not None:
            camera_obj.release()
            self._current_camera_id = -1
            del self._cameras_dict[device_id]
            return True
        else:
            return False

    def set_current_camera_capture_resolution(self, width, height):
        """Set the capture resolution of the current camera.

        :param width: The width in pixels.
        :type width: int

        :param height: The height in pixels.
        :type height: int

        :return: Whether or not this operation was possible.
        :rtype: bool
        """
        if (current_camera := self.get_camera()) is not None:
            current_camera.stop()
            current_camera.set_capture_property(cv.CAP_PROP_FRAME_WIDTH, width)
            current_camera.set_capture_property(cv.CAP_PROP_FRAME_HEIGHT, height)
            current_camera.start()
            return True
        else:
            return False

    def set_current_camera_prop_value(self, property_id, value):
        """Set the current camera property value.

        :param property_id: The cv.CAM_PROP_ value for this property.
        :type property_id: int

        :param value: The value.
        :type value: int

        :return: Whether or not this operation was possible.
        :rtype: bool
        """
        if (current_camera := self.get_camera()) is not None:
            current_camera.set_capture_property(property_id, value)
            return True
        else:
            return False

    def set_current_camera_name(self, name):
        """Set the current camera name.

        :param name: The camera name.
        :type name: str

        :return: Whether or not this operation was possible.
        :rtype: bool
        """
        if (current_camera := self.get_camera()) is not None:
            current_camera.name = name
            return True
        else:
            return False

    def set_current_camera_model_name(self, model_name):
        """Set the current camera model name.

        :param model_name: The camera model name.
        :type name: str

        :return: Whether or not this operation was possible.
        :rtype: bool
        """
        if (current_camera := self.get_camera()) is not None:
            current_camera.model_name = model_name
            return True
        else:
            return False

    def set_current_camera_device_id(self, device_id):
        """Set the device id of the current camera to this value.

        :param device_id: The device id.
        :type device_id: int

        :return: Whether or not this operation was possible.
        :rtype: bool
        """
        if (current_camera := self.get_camera()) is not None:
            if device_id != current_camera.device_id and device_id in self.get_available_device_ids_list():
                self._cameras_dict[device_id] = self._cameras_dict[current_camera.device_id]
                del self._cameras_dict[current_camera.device_id]
                current_camera.device_id = device_id
                self._current_camera_id = device_id
                return True
        return False

    def release_all(self):
        """Release all active cameras."""
        for _, camera_obj in self._cameras_dict.items():
            camera_obj.release()
