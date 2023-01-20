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
        self._no_camera_trigger = False

        self._init_ui()


    def _init_ui(self):
        """Initialize the UI."""
        self.ui = uic.loadUi(os.path.join(os.path.dirname(__file__), "ui", "calibration_widget.ui"))
        self.setWindowTitle("Camera Calibration")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.ui)
        self.setLayout(layout)

        self.ui.combo_camera_device_id.addItems(self.get_available_device_ids_list(as_list_of_str=True))

        self._init_connections()
        self.show()

    def _init_connections(self):
        """Initialize connections."""
        self.ui.push_add_camera.clicked.connect(self.add_camera)
        # self.ui.push_pause.clicked.connect(self.pause_camera)
        self.ui.push_quit.clicked.connect(self.close)
        # self.ui.spin_device_id.valueChanged.connect(self.change_device_id)
        # self.ui.combo_resolution.currentTextChanged.connect(self.change_resolution)
        # self.ui.spin_exposure.valueChanged.connect(self.change_exposure)
        # self.ui.spin_focus.valueChanged.connect(self.change_focus)

        self._ticker.tick.connect(self.tick)

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

    @QtCore.pyqtSlot(float)
    def tick(self, tick_time):
        """Refresh viewport.

        :param tick_time: Time since the begining of the tick start.
        :type tick_time: float
        """
        current_camera = self._cameras_dict.get(self._current_camera_id)
        if current_camera is None:
            return

        camera_frame, info_str = self._cameras_dict.get_frame(return_info=True)
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

        if self.ui.check_actual_frame_size.isChecked():
            self.ui.label_image.resize(image.width(), image.height())
        else:
            image = image.scaledToWidth(self.ui.scroll_image.size().width() - 20)
        self.ui.label_image.setPixmap(QtGui.QPixmap.fromImage(image))

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
        new_camera = aiw_camera.Camera(device_id=device_id)
        self._cameras_dict[device_id] = new_camera

        # add to list
        self.ui.list_cameras.addItem(f'Camera ID: {device_id}, "{new_camera.name}", "{new_camera.name}"')

        # select the camera item in list


    # @QtCore.pyqtSlot()
    # def start_camera(self):
    #     self._ticker.stop()
    #     self._ticker.wait()
    #     self.camera.start()
    #     self._ticker.start()

    # @QtCore.pyqtSlot()
    # def pause_camera(self):
    #     self._ticker.stop()
    #     self._ticker.wait()
    #     self.camera.stop()

    # @QtCore.pyqtSlot()
    # def close(self):
    #     self._ticker.stop()
    #     self._ticker.wait()
    #     self.camera.release()
    #     super().close()

    # @QtCore.pyqtSlot(int)
    # def change_device_id(self, device_id):
    #     self.camera.device_id = device_id
    #     self.start_camera()

    # @QtCore.pyqtSlot(str)
    # def change_resolution(self, resolution_text):
    #     was_running = self.camera.is_running()
    #     width_str, height_str = resolution_text.split("x")
    #     if was_running:
    #         self.camera.stop()
    #     self.camera.set_capture_property(cv.CAP_PROP_FRAME_WIDTH, int(width_str))
    #     self.camera.set_capture_property(cv.CAP_PROP_FRAME_HEIGHT, int(height_str))
    #     if was_running:
    #         self.camera.start()

    # @QtCore.pyqtSlot(int)
    # def change_exposure(self, exposure):
    #     self.camera.set_capture_property(cv.CAP_PROP_EXPOSURE, exposure)

    # @QtCore.pyqtSlot(int)
    # def change_focus(self, focus):
    #     self.camera.set_capture_property(cv.CAP_PROP_FOCUS, focus)
