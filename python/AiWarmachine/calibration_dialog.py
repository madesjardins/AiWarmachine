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
"""Camera calibration dialog to setup your cameras."""
import sys
import os
import traceback
import re
from functools import partial

from PyQt6 import QtWidgets, QtCore, QtGui, uic
import cv2 as cv

from . import camera as aiw_camera
from . import common as aiw_common
from . import constants as aiw_constants
from . import tick_generator as aiw_tick


class CalibrationDialog(QtWidgets.QDialog):
    """Calibration dialog is used to calibrate your cameras."""

    def __init__(self, parent=None):
        """Initialize.

        :param parent: The parent widget. (None)
        :type parent: :class:`QWidget`
        """
        super().__init__(parent=parent)

        self._animation_frame = 0
        self._cameras_dict = {}
        self._current_camera_id = -1
        self._ticker = aiw_tick.TickGenerator(30.0)
        self._disable_camera_settings_change = False

        self._init_ui()
        self._init_connections()
        self.show()

    def _init_ui(self):
        """Initialize the UI."""
        self.ui = uic.loadUi(os.path.join(os.path.dirname(__file__), "ui", "calibration_widget.ui"))
        self.setWindowTitle("Camera Calibration")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.ui)
        self.setLayout(layout)

        self.fill_current_camera_settings(default=True)

    def _init_connections(self):
        """Initialize connections."""
        self.ui.push_quit.clicked.connect(self.close)

        self.ui.push_add_camera.clicked.connect(self.add_camera)
        self.ui.push_delete_camera.clicked.connect(self.delete_camera)
        self.ui.list_cameras.itemSelectionChanged.connect(self.set_viewport_to_selected)

        # camera settings
        self.ui.edit_camera_name.textEdited.connect(self.set_current_camera_name)
        self.ui.edit_camera_model_name.textEdited.connect(self.set_current_camera_model_name)
        self.ui.combo_camera_device_id.currentTextChanged.connect(self.set_current_camera_device_id)
        self.ui.combo_camera_capture_resolution.currentTextChanged.connect(self.set_camera_capture_resolution)
        self.ui.spin_camera_exposure.valueChanged.connect(partial(self.set_camera_prop_value, cv.CAP_PROP_EXPOSURE))
        self.ui.slider_camera_focus.valueChanged.connect(partial(self.set_camera_prop_value, cv.CAP_PROP_FOCUS))
        self.ui.push_camera_focus_reset.clicked.connect(partial(self.reset_camera_slider, self.ui.slider_camera_focus, 0))
        self.ui.slider_camera_brightness.valueChanged.connect(partial(self.set_camera_prop_value, cv.CAP_PROP_BRIGHTNESS))
        self.ui.push_camera_brightness_reset.clicked.connect(partial(self.reset_camera_slider, self.ui.slider_camera_brightness, 128))
        self.ui.slider_camera_contrast.valueChanged.connect(partial(self.set_camera_prop_value, cv.CAP_PROP_CONTRAST))
        self.ui.push_camera_contrast_reset.clicked.connect(partial(self.reset_camera_slider, self.ui.slider_camera_contrast, 128))
        self.ui.slider_camera_gain.valueChanged.connect(partial(self.set_camera_prop_value, cv.CAP_PROP_GAIN))
        self.ui.push_camera_gain_reset.clicked.connect(partial(self.reset_camera_slider, self.ui.slider_camera_gain, 128))
        self.ui.slider_camera_saturation.valueChanged.connect(partial(self.set_camera_prop_value, cv.CAP_PROP_SATURATION))
        self.ui.push_camera_saturation_reset.clicked.connect(partial(self.reset_camera_slider, self.ui.slider_camera_saturation, 128))
        self.ui.slider_camera_sharpness.valueChanged.connect(partial(self.set_camera_prop_value, cv.CAP_PROP_SHARPNESS))
        self.ui.push_camera_sharpness_reset.clicked.connect(partial(self.reset_camera_slider, self.ui.slider_camera_sharpness, 128))

        # self.ui.edit_camera_model_name = current_camera.model_name
        # self.ui.spin_device_id.valueChanged.connect(self.change_device_id)

        # self.ui.spin_exposure.valueChanged.connect(self.change_exposure)
        # self.ui.spin_focus.valueChanged.connect(self.change_focus)

        self._ticker.tick.connect(self.tick)

    def update_current_camera_item_label(self):
        """Update the current camera item's label."""
        if (
            (current_camera := self._cameras_dict.get(self._current_camera_id)) is not None and
            (camera_item := self.get_current_camera_item()) is not None
        ):
            camera_item.setText(f'Camera ID: {current_camera.device_id}, "{current_camera.name}", "{current_camera.model_name}"')

    def get_current_camera(self):
        """Get the camera with current device id.

        :return: Camera.
        :rtype: :class:`Camera`
        """
        return self._cameras_dict.get(self._current_camera_id)

    def get_current_camera_item(self):
        """Get the current camera item if any.

        :return: The camera item.
        :rtype: :class:`QListWidgetItem`
        """
        if selected_items := self.ui.list_cameras.selectedItems():
            return selected_items[0]
        return None

    @QtCore.pyqtSlot(str)
    def set_current_camera_name(self, name):
        """Set the current camera name.

        :param name: The camera name.
        :type name: str
        """
        if self._disable_camera_settings_change:
            return
        if (current_camera := self._cameras_dict.get(self._current_camera_id)) is not None:
            current_camera.name = name
            self.update_current_camera_item_label()

    @QtCore.pyqtSlot(str)
    def set_current_camera_model_name(self, model_name):
        """Set the current camera model name.

        :param model_name: The camera model name.
        :type name: str
        """
        if self._disable_camera_settings_change:
            return
        if (current_camera := self._cameras_dict.get(self._current_camera_id)) is not None:
            current_camera.model_name = model_name
            self.update_current_camera_item_label()

    @QtCore.pyqtSlot(str)
    def set_current_camera_device_id(self, device_id_str):
        """Set the device id of the current camera to this value.

        :param device_id_str: The device id as a str.
        :type device_id_str: str
        """
        if self._disable_camera_settings_change:
            return
        if (current_camera := self._cameras_dict.get(self._current_camera_id)) is not None:
            device_id = int(device_id_str)
            if device_id != current_camera.device_id and device_id in self.get_available_device_ids_list():
                self.pause_ticker()
                self._cameras_dict[device_id] = self._cameras_dict[current_camera.device_id]
                del self._cameras_dict[current_camera.device_id]
                current_camera.device_id = device_id
                self._current_camera_id = device_id
                self.update_current_camera_item_label()
                self.start_ticker()

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
        return [cast_class(_i) for _i in aiw_constants.DEFAULT_DEVICE_IDS_LIST if _i not in self._cameras_dict]

    @QtCore.pyqtSlot(QtGui.QCloseEvent)
    def closeEvent(self, a0):
        """Stop ticker and release all cameras."""
        try:
            self._ticker.stop()
            self._ticker.wait()
            for _, camera in self._cameras_dict.items():
                camera.release()
        except Exception:
            traceback.print_exc()
        return super().closeEvent(a0)

    @QtCore.pyqtSlot()
    def close(self):
        """Close dialog."""
        return super().close()

    def start_ticker(self):
        """Start the ticker."""
        self._ticker.stop()
        self._ticker.wait()
        self._ticker.start()

    def pause_ticker(self):
        """Stop the ticker."""
        self._ticker.stop()
        self._ticker.wait()

    @QtCore.pyqtSlot(float)
    def tick(self, tick_time):
        """Refresh viewport.

        :param tick_time: Time since the begining of the tick start.
        :type tick_time: float
        """
        current_camera = self._cameras_dict.get(self._current_camera_id)
        if current_camera is None:
            return

        camera_frame, info_str = current_camera.get_frame(return_info=True)
        if camera_frame is None:
            frame = aiw_common.get_frame_with_text("Please wait" + "." * (int(self._animation_frame / 30) % 4))
            image = QtGui.QImage(
                frame,
                frame.shape[1],
                frame.shape[0],
                frame.strides[0],
                QtGui.QImage.Format.Format_BGR888
            )
            self._animation_frame += 1

        else:
            self._animation_frame = 0
            image = QtGui.QImage(
                camera_frame,
                camera_frame.shape[1],
                camera_frame.shape[0],
                camera_frame.strides[0],
                QtGui.QImage.Format.Format_BGR888
            )
            self.ui.edit_camera_effective_resolution.setText(info_str)

        if self.ui.check_display_actual_resolution.isChecked():
            self.ui.label_viewport_image.resize(image.width(), image.height())
        else:
            image = image.scaledToWidth(self.ui.scroll_viewport.size().width() - 20)
        self.ui.label_viewport_image.setPixmap(QtGui.QPixmap.fromImage(image))

    def get_selected_device_id(self):
        """Get the device id of the selected camera.

        :return: The divice id or None if no selection.
        :rtype: int
        """
        if self.ui.list_cameras.selectedItems():
            camera_list_item = self.ui.list_cameras.selectedItems()[0]
            if re_match_device_id := re.match("Camera ID: (?P<device_id>\\d+),", camera_list_item.text()):
                return int(re_match_device_id.group("device_id"))

        return None

    def fill_current_camera_settings(self, default=False):
        """Fill current camera settings fields.

        :param default: If set to True, will fill the fields using default values. (False)
        :type default: bool
        """
        self._disable_camera_settings_change = True
        if default:
            self.ui.edit_camera_name.setText("")
            self.ui.combo_camera_device_id.clear()
            self.ui.combo_camera_device_id.addItems(self.get_available_device_ids_list(as_list_of_str=True))
            self.ui.edit_camera_model_name.setText("")

        elif (current_camera := self.get_current_camera()) is not None:
            self.ui.edit_camera_name.setText(current_camera.name)
            self.ui.edit_camera_model_name.setText(current_camera.model_name)
            device_id_str = str(current_camera.device_id)
            available_device_ids_list = sorted(set(self.get_available_device_ids_list(as_list_of_str=True) + [device_id_str]))
            self.ui.combo_camera_device_id.clear()
            self.ui.combo_camera_device_id.addItems(
                available_device_ids_list
            )
            self.ui.combo_camera_device_id.setCurrentIndex(available_device_ids_list.index(device_id_str))

        self._disable_camera_settings_change = False

    @QtCore.pyqtSlot()
    def set_viewport_to_selected(self):
        """Set the viewport to the selected camera in the list."""
        self.pause_ticker()
        if (device_id := self.get_selected_device_id()) is not None:
            if (camera := self._cameras_dict.get(device_id)) is not None:
                if not camera.is_running():
                    camera.start()
                self._current_camera_id = device_id
                self.start_ticker()
                self.fill_current_camera_settings()

            self.ui.push_delete_camera.setEnabled(True)
        else:
            self.ui.push_delete_camera.setEnabled(False)

    @QtCore.pyqtSlot()
    def add_camera(self):
        """Add a new camera to the list."""
        available_device_ids_list = self.get_available_device_ids_list(as_list_of_str=True)
        if not available_device_ids_list:
            aiw_common.message_box(
                title="Add Camera",
                text="Unable to add a new camera.",
                info_text="No device id available.",
                icon_name="Warning",
                button_names_list=["Close"]
            )
            return

        device_id_str, is_valid = QtWidgets.QInputDialog.getItem(
            self,
            "Question",
            "Device ID to use:",
            available_device_ids_list,
            0,
            False
        )
        if not is_valid:
            return

        device_id = int(device_id_str)

        # create the camera objects
        new_camera = aiw_camera.Camera(device_id=device_id, debug=True)
        self._cameras_dict[device_id] = new_camera

        # add to list
        self.ui.list_cameras.addItem(f'Camera ID: {device_id}, "{new_camera.name}", "{new_camera.model_name}"')

        # select the new camera item in list
        self.ui.list_cameras.setCurrentRow(self.ui.list_cameras.count() - 1)

    @QtCore.pyqtSlot()
    def delete_camera(self):
        """Delete the selected camera."""
        try:
            self.pause_ticker()
            if (device_id := self.get_selected_device_id()) is not None:
                if (camera := self._cameras_dict.get(device_id)) is not None:
                    camera.release()
                    self._current_camera_id = -1
                    del self._cameras_dict[device_id]
                self.ui.list_cameras.takeItem(self.ui.list_cameras.currentRow())
        except Exception:
            traceback.print_exc()

    @QtCore.pyqtSlot(str)
    def set_camera_capture_resolution(self, resolution_str):
        """Set the current camera capture resolution.

        :param resolution_str: Resolution as a str '{width}x{height}'.
        :type resolution_str: str
        """
        if self._disable_camera_settings_change:
            return
        if (current_camera := self._cameras_dict.get(self._current_camera_id)) is not None:
            self.pause_ticker()
            width_str, height_str = resolution_str.split("x")
            current_camera.stop()
            current_camera.set_capture_property(cv.CAP_PROP_FRAME_WIDTH, int(width_str))
            current_camera.set_capture_property(cv.CAP_PROP_FRAME_HEIGHT, int(height_str))
            current_camera.start()
            self.start_ticker()

    @QtCore.pyqtSlot(int, int)
    def set_camera_prop_value(self, property, value):
        """Set the current camera property value.

        :param property: The cv.CAM_PROP_ value for this property.
        :type property: int

        :param value: The value.
        :type value: int
        """
        if self._disable_camera_settings_change:
            return
        if (current_camera := self._cameras_dict.get(self._current_camera_id)) is not None:
            current_camera.set_capture_property(property, value)

    @QtCore.pyqtSlot(QtWidgets.QSlider, int)
    def reset_camera_slider(self, slider, default_value):
        """Reset the slider to its default value..

        :param slider: The slider to reset.
        :type slider: :class:`QSlider`

        :param default_value: The default value.
        :type default_value: int
        """
        slider.setValue(default_value)
