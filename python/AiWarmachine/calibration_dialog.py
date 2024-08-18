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

import os
import traceback
import re
from functools import partial
from datetime import datetime
import json
import time
from pprint import pprint

from PyQt6 import QtWidgets, QtCore, QtGui, uic
import cv2 as cv
import numpy as np

from . import camera
from . import common
from . import constants
from . import tick_generator
from . import game_table
from . import model_detection
from . import viewport_label
from . import qr_detection


class CalibrationDialog(QtWidgets.QDialog):
    """Calibration dialog is used to calibrate your cameras."""

    analyze_qr_image = QtCore.pyqtSignal(object, int, int, int, int)

    def __init__(self, parent=None):
        """Initialize.

        :param parent: The parent widget. (None)
        :type parent: :class:`QWidget`
        """
        super().__init__(parent=parent)

        self._animation_frame = 0
        self._cameras_dict = {}
        self._current_camera_id = -1
        self._ticker = tick_generator.TickGenerator(30.0)
        self._disable_camera_settings_change = False
        self._disable_table_change = False
        self._calibration_packages_dict = {
            'top': None,
            'front': None,
            'side': None,
            'pose': None
        }
        self._last_valid_calibration_pkg = None
        self._in_calibration = False
        self._table = game_table.GameTable()
        self._image_overlay = None
        self._qr_detection_overlay = None
        self._overlay_need_update = True
        self._previous_time = 0
        self._model_dectector = None
        # TEMP Commented !!
        # self._init_model_detection()
        self._detected_models_list = []
        self._table_corner_points_list = []
        self._qr_detector = qr_detection.QRDetector()
        self.latest_qr_detection_data = {}
        self._skip_for_n_ticks = 0
        self._init_ui()
        self._init_connections()
        self.show()

    def _init_ui(self):
        """Initialize the UI."""
        self.ui = uic.loadUi(os.path.join(os.path.dirname(__file__), "ui", "calibration_widget.ui"))
        self.setWindowTitle("Calibration")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.ui)
        self.setLayout(layout)

        self.ui.label_viewport_image = viewport_label.ViewportLabel(self.ui.scroll_viewport_widget)
        self.ui.scroll_viewport_widget.layout().addWidget(self.ui.label_viewport_image)

        self.fill_current_camera_settings(default=True)
        self.set_enabled_for_calibrated_camera()

        if constants.IS_LINUX:
            self.ui.slider_camera_focus.hide()
            self.ui.label_camera_focus.hide()
            self.ui.spin_camera_exposure.setRange(3, 2047)
            self.ui.spin_camera_exposure.setSingleStep(25)
            self.ui.spin_camera_exposure.setValue(250)

    def _init_connections(self):
        """Initialize connections."""
        self.ui.push_quit.clicked.connect(self.close)

        self.ui.push_add_camera.clicked.connect(self.add_camera)
        self.ui.push_delete_camera.clicked.connect(self.delete_camera)
        self.ui.list_cameras.itemSelectionChanged.connect(self.set_viewport_to_selected)
        self.ui.push_save_camera.clicked.connect(self.camera_save)
        self.ui.push_load_camera.clicked.connect(self.camera_load)

        # camera settings
        self.ui.edit_camera_name.textEdited.connect(self.set_current_camera_name)
        self.ui.edit_camera_model_name.textEdited.connect(self.set_current_camera_model_name)
        self.ui.combo_camera_device_id.currentTextChanged.connect(self.set_current_camera_device_id)
        self.ui.combo_camera_capture_resolution.currentTextChanged.connect(self.set_camera_capture_resolution)
        self.ui.spin_camera_exposure.valueChanged.connect(partial(self.set_camera_prop_value, cv.CAP_PROP_EXPOSURE))
        self.ui.slider_camera_focus.valueChanged.connect(partial(self.set_camera_prop_value, cv.CAP_PROP_FOCUS))
        self.ui.push_camera_focus_reset.clicked.connect(partial(self.reset_camera_slider, self.ui.slider_camera_focus, 0))
        self.ui.slider_camera_zoom.valueChanged.connect(partial(self.set_camera_prop_value, cv.CAP_PROP_ZOOM))
        self.ui.push_camera_zoom_reset.clicked.connect(partial(self.reset_camera_slider, self.ui.slider_camera_zoom, 100))
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

        # calibration
        self.ui.push_calibration_image_top.clicked.connect(partial(self.trigger_calibration_image, "top"))
        self.ui.push_calibration_image_front.clicked.connect(partial(self.trigger_calibration_image, "front"))
        self.ui.push_calibration_image_side.clicked.connect(partial(self.trigger_calibration_image, "side"))
        self.ui.push_calibration_image_pose.clicked.connect(partial(self.trigger_calibration_image, "pose"))
        self.ui.push_calibrate.clicked.connect(self.calibrate)
        self.ui.push_pose.clicked.connect(self.pose)
        self.ui.push_uncalibrate.clicked.connect(self.uncalibrate)

        # table
        self.ui.spin_table_w.valueChanged.connect(self.update_table_dimensions)
        self.ui.spin_table_h.valueChanged.connect(self.update_table_dimensions)
        self.ui.combo_table_border_color.currentIndexChanged.connect(self.update_table_border_color)
        self.ui.spin_table_border_color_alpha.valueChanged.connect(self.update_table_border_color)
        self.ui.double_table_t_x.valueChanged.connect(self.update_table_transforms)
        self.ui.double_table_t_y.valueChanged.connect(self.update_table_transforms)
        self.ui.double_table_t_z.valueChanged.connect(self.update_table_transforms)
        self.ui.double_table_r_x.valueChanged.connect(self.update_table_transforms)
        self.ui.double_table_r_y.valueChanged.connect(self.update_table_transforms)
        self.ui.double_table_r_z.valueChanged.connect(self.update_table_transforms)
        self.ui.push_table_reset.clicked.connect(self.reset_table_transforms)
        self.ui.push_table_save.clicked.connect(self.table_save)
        self.ui.push_table_load.clicked.connect(self.table_load)
        self.ui.edit_table_name.textEdited.connect(self.set_table_name)

        # snapshot
        self.ui.push_snapshot_save.clicked.connect(self.snapshot_save)

        # tick
        self._ticker.tick.connect(self.tick)

        # model detection
        # self.ui.check_model_detection.clicked.connect(self._start_stop_model_detection)

        # QR Detection
        self._qr_detector.latest_data_ready.connect(self.update_latest_qr_detection_data)
        self.analyze_qr_image.connect(self._qr_detector.set_image)

    @QtCore.pyqtSlot(dict, int, int, int, int)
    def update_latest_qr_detection_data(self, latest_data, offset_x, offset_y, width, height):
        """Update latest qr detection data."""
        if len(latest_data) != len(self.latest_qr_detection_data):  # TODO: test center diff > epsilon
            self.latest_qr_detection_data = latest_data
            image_size = QtCore.QSize(width, height)
            qr_detection_overlay = QtGui.QImage(image_size, QtGui.QImage.Format.Format_ARGB32_Premultiplied)
            painter = QtGui.QPainter(qr_detection_overlay)
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode.CompositionMode_Source)
            painter.fillRect(qr_detection_overlay.rect(), QtCore.Qt.GlobalColor.transparent)
            detect_brush = QtGui.QBrush()
            painter.setBrush(detect_brush)
            detect_pen = QtGui.QPen(QtCore.Qt.GlobalColor.red, 4, QtCore.Qt.PenStyle.SolidLine)
            painter.setPen(detect_pen)
            for qr_message, qr_data in self.latest_qr_detection_data.items():
                for vert in qr_data['bounds']:
                    painter.drawPoint(int(offset_x + vert[0]), int(offset_y + vert[1]))
            painter.end()
            self._qr_detection_overlay = qr_detection_overlay
        else:
            self.latest_qr_detection_data = latest_data

    def update_current_camera_item_label(self):
        """Update the current camera item's label."""
        if (
            (current_camera := self.get_current_camera()) is not None and
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
        if (current_camera := self.get_current_camera()) is not None:
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
        if (current_camera := self.get_current_camera()) is not None:
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
        if (current_camera := self.get_current_camera()) is not None:
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
        return [cast_class(_i) for _i in constants.DEFAULT_DEVICE_IDS_LIST if _i not in self._cameras_dict]

    @QtCore.pyqtSlot(QtGui.QCloseEvent)
    def closeEvent(self, a0):
        """Stop ticker and release all cameras."""
        try:
            self._ticker.stop()
            self._ticker.wait()
            self._qr_detector.stop()
            self._qr_detector.wait()
            for _, camera_obj in self._cameras_dict.items():
                camera_obj.release()
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

    @QtCore.pyqtSlot(float, float)
    def tick(self, running_time, time_interval):
        """Refresh viewport.

        :param tick_time: Time since the begining of the tick start.
        :type tick_time: float
        """
        current_camera = self.get_current_camera()
        if current_camera is None:
            return

        if self._skip_for_n_ticks > 0:
            self._skip_for_n_ticks -= 1
            return

        start_process = time.time()

        composite_overlay = False
        camera_frame, info_str = current_camera.get_frame(return_info=True)

        # -- NO IMAGE in FEED --
        if camera_frame is None:
            frame = common.get_frame_with_text("Please wait" + "." * (int(self._animation_frame / 30) % 4))
            image = QtGui.QImage(
                frame,
                frame.shape[1],
                frame.shape[0],
                frame.strides[0],
                QtGui.QImage.Format.Format_BGR888
            )
            self._animation_frame += 1
            if self.ui.check_display_undistorted.isChecked():
                self.ui.check_display_undistorted.setCheckState(QtCore.Qt.CheckState.Unchecked)
        else:

            # -- VALID IMAGE FEED --
            self._animation_frame = 0

            # -- IN CALIBRATION --
            if self._in_calibration:
                gray = cv.cvtColor(camera_frame, cv.COLOR_BGR2GRAY)

                checkerboard_dim = (
                    self.ui.spin_number_of_squares_w.value() - 1,
                    self.ui.spin_number_of_squares_h.value() - 1
                )
                ret, corners = cv.findChessboardCorners(gray, checkerboard_dim, flags=cv.CALIB_CB_FAST_CHECK)
                if ret:
                    self._last_valid_calibration_pkg = gray, corners
                    camera_frame = cv.drawChessboardCorners(
                        cv.cvtColor(gray, cv.COLOR_GRAY2BGR),
                        checkerboard_dim,
                        corners,
                        ret
                    )
                if self.ui.check_display_undistorted.isChecked():
                    self.ui.check_display_undistorted.setCheckState(QtCore.Qt.CheckState.Unchecked)

            # -- CALIBRATED -> UNDISTORT IMAGE --
            elif current_camera.is_calibrated():
                if not self.ui.check_display_undistorted.isChecked():
                    self.ui.check_display_undistorted.setCheckState(QtCore.Qt.CheckState.Checked)
                camera_frame = current_camera.undistort(camera_frame)

                # NO OVERLAY ANYMORE
                # if current_camera.is_posed():
                #     composite_overlay = True
                #     # recreate overlay if needed
                #     if (
                #         self._overlay_need_update or
                #         self._image_overlay is None or
                #         self._image_overlay.width() != camera_frame.shape[1] or
                #         self._image_overlay.height() != camera_frame.shape[0]
                #     ):
                #         self.update_axes_and_table_layer(camera_frame.shape[1], camera_frame.shape[0])

            # -- RESET DISTORTION CHECK --
            elif self.ui.check_display_undistorted.isChecked():
                self.ui.check_display_undistorted.setCheckState(QtCore.Qt.CheckState.Unchecked)

            # -- STORE LATEST IMAGE as QIMAGE--
            self.latest_image = QtGui.QImage(
                camera_frame,
                camera_frame.shape[1],
                camera_frame.shape[0],
                camera_frame.strides[0],
                QtGui.QImage.Format.Format_BGR888
            )

            self.ui.edit_camera_effective_resolution.setText(info_str)

            # -- QR DETECTOR --
            if self.ui.check_qr_detection.isChecked():
                min_x = 0  # min([_p.x() for _p in self._table_corner_points_list])
                min_y = 0  # min([_p.y() for _p in self._table_corner_points_list])
                max_x = camera_frame.shape[1] - 1  # max([_p.x() for _p in self._table_corner_points_list])
                max_y = camera_frame.shape[0] - 1  # max([_p.y() for _p in self._table_corner_points_list])

                min_x = int(min(max(0, min_x), camera_frame.shape[1] - 1))
                min_y = int(min(max(0, min_y), camera_frame.shape[0] - 1))
                max_x = int(min(max(0, max_x), camera_frame.shape[1] - 1))
                max_y = int(min(max(0, max_y), camera_frame.shape[0] - 1))

                self.analyze_qr_image.emit(cv.cvtColor(camera_frame, cv.COLOR_BGR2GRAY), min_x, min_y, max_x, max_y)
                if not self._qr_detector.is_running():
                    self._qr_detector.start()

                if self.latest_qr_detection_data:
                    composite_overlay = True

            else:
                self._qr_detector.stop()
                self._qr_detector.wait()
                self._qr_detector.reset()
                self.latest_qr_detection_data = {}
                composite_overlay = False

            if (
                composite_overlay and
                self.ui.check_qr_detection.isChecked() and
                self.latest_qr_detection_data and
                self._qr_detection_overlay is not None
            ):
                # image = self.latest_image
                image = common.composite_images(self.latest_image, self._qr_detection_overlay)

            else:
                image = self.latest_image

        if self.ui.check_display_actual_resolution.isChecked():
            self.ui.label_viewport_image.resize(image.width(), image.height())
        else:
            image = image.scaledToWidth(self.ui.scroll_viewport.size().width() - 20)

        # Show image in viewport
        self.ui.label_viewport_image.setPixmap(QtGui.QPixmap.fromImage(image))
        self.ui.label_viewport_image.repaint()
        time_delay = time.time() - self._previous_time
        fps = 1.0 / max(0.0001, time_delay)
        self._previous_time = time.time()
        self.ui.edit_viewport_resolution.setText(f"{image.width()}x{image.height()} @ {fps:0.1f}")

        # skip next frame is this one took too much time
        process_time_x2 = 2 * (time.time() - start_process)
        if process_time_x2 > time_interval:
            self.skip_for_n_ticks = int(process_time_x2 / time_interval)

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
            width = current_camera.get_capture_property(common.get_capture_property_id("Width"))
            height = current_camera.get_capture_property(common.get_capture_property_id("Height"))
            capture_resolution_str = f"{width}x{height}"
            index = self.ui.combo_camera_capture_resolution.findText(capture_resolution_str)
            if index > -1:
                self.ui.combo_camera_capture_resolution.setCurrentIndex(index)
            else:
                self.ui.combo_camera_capture_resolution.addItem(capture_resolution_str)
                self.ui.combo_camera_capture_resolution.setCurrentIndex(self.ui.combo_camera_capture_resolution.count() - 1)
            self.ui.spin_camera_exposure.setValue(
                current_camera.get_capture_property(common.get_capture_property_id("Exposure"))
            )
            if not constants.IS_LINUX:
                self.ui.slider_camera_focus.setValue(
                    current_camera.get_capture_property(common.get_capture_property_id("Focus"))
                )
            self.ui.slider_camera_zoom.setValue(
                current_camera.get_capture_property(common.get_capture_property_id("Zoom"))
            )
            self.ui.slider_camera_brightness.setValue(
                current_camera.get_capture_property(common.get_capture_property_id("Brightness"))
            )
            self.ui.slider_camera_contrast.setValue(
                current_camera.get_capture_property(common.get_capture_property_id("Contrast"))
            )
            self.ui.slider_camera_gain.setValue(
                current_camera.get_capture_property(common.get_capture_property_id("Gain"))
            )
            self.ui.slider_camera_saturation.setValue(
                current_camera.get_capture_property(common.get_capture_property_id("Saturation"))
            )
            self.ui.slider_camera_sharpness.setValue(
                current_camera.get_capture_property(common.get_capture_property_id("Sharpness"))
            )

        self._disable_camera_settings_change = False

    @QtCore.pyqtSlot()
    def set_viewport_to_selected(self):
        """Set the viewport to the selected camera in the list."""
        self.pause_ticker()
        if (device_id := self.get_selected_device_id()) is not None:
            if (camera_obj := self._cameras_dict.get(device_id)) is not None:
                if not camera_obj.is_running():
                    camera_obj.start()
                self._current_camera_id = device_id
                self.start_ticker()
                self.fill_current_camera_settings()

            self.ui.push_delete_camera.setEnabled(True)
        else:
            self.ui.push_delete_camera.setEnabled(False)
        self.set_enabled_for_calibrated_camera()

    @QtCore.pyqtSlot()
    def add_camera(self):
        """Add a new camera to the list."""
        available_device_ids_list = self.get_available_device_ids_list(as_list_of_str=True)
        if not available_device_ids_list:
            common.message_box(
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
        new_camera = camera.Camera(device_id=device_id, debug=True)
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
                if (camera_obj := self._cameras_dict.get(device_id)) is not None:
                    camera_obj.release()
                    self._current_camera_id = -1
                    del self._cameras_dict[device_id]
                self.ui.list_cameras.takeItem(self.ui.list_cameras.currentRow())
        except Exception:
            traceback.print_exc()
        self.set_enabled_for_calibrated_camera()

    @QtCore.pyqtSlot(str)
    def set_camera_capture_resolution(self, resolution_str):
        """Set the current camera capture resolution.

        :param resolution_str: Resolution as a str '{width}x{height}'.
        :type resolution_str: str
        """
        if self._disable_camera_settings_change:
            return
        if (current_camera := self.get_current_camera()) is not None:
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
        if (current_camera := self.get_current_camera()) is not None:
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

    @QtCore.pyqtSlot(str)
    def trigger_calibration_image(self, view_name):
        """Trigger the countdown to take a calibration image.

        :param view_name: The name of the view, choices are: ['top', 'front', 'side', 'pose'].
        :type view_name: str
        """
        self._last_valid_calibration_pkg = None
        self._in_calibration = True
        QtCore.QTimer.singleShot(3000, partial(self.set_calibration_image, view_name))

    @QtCore.pyqtSlot(str)
    def set_calibration_image(self, view_name):
        """Set a calibration image.

        :param view_name: The name of the view, choices are: ['top', 'front', 'side', 'pose'].
        :type view_name: str
        """
        self._in_calibration = False
        if self._last_valid_calibration_pkg is not None:
            self._calibration_packages_dict[view_name] = self._last_valid_calibration_pkg
            self._last_valid_calibration_pkg = None

            push_button = getattr(self.ui, f"push_calibration_image_{view_name}")
            push_button.setText("")
            frame_gray, _ = self._calibration_packages_dict[view_name]
            frame = cv.cvtColor(frame_gray, cv.COLOR_GRAY2BGR)

            image = QtGui.QImage(
                frame,
                frame.shape[1],
                frame.shape[0],
                frame.strides[0],
                QtGui.QImage.Format.Format_BGR888
            )
            pix = QtGui.QPixmap.fromImage(
                image.scaled(
                    push_button.width() - 10,
                    push_button.height() - 10,
                    aspectRatioMode=QtCore.Qt.AspectRatioMode.KeepAspectRatio
                )
            )
            push_button.setIcon(QtGui.QIcon(pix))
            push_button.setIconSize(pix.rect().size())

        self.set_enabled_for_calibrated_camera()

    @QtCore.pyqtSlot()
    def calibrate(self):
        """Calibrate the camera using the top, front and side views."""
        current_camera = self.get_current_camera()
        if current_camera is None:
            print("No current camera")
            return

        checkerboard_3d_reference_points_array = self.get_checkerboard_3d_reference_points(use_checkerboard_thickness=False)
        checkerboard_3d_points_list = []
        checkerboard_2d_points_list = []
        image_resolution = None
        for view_name in ['top', 'front', 'side']:
            frame_gray, corners = self._calibration_packages_dict[view_name]
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

        try:
            mean_error = current_camera.calibrate(
                checkerboard_3d_points_list,
                checkerboard_2d_points_list,
                image_resolution
            )
            print(f"Calibration error: {mean_error}")
        except Exception:
            traceback.print_exc()

        self.set_enabled_for_calibrated_camera()

    @QtCore.pyqtSlot()
    def pose(self):
        """Calculate camera pose using pose view."""
        current_camera = self.get_current_camera()
        if current_camera is None:
            print("No current camera")
            return
        elif not current_camera.is_calibrated():
            print("Current camera is not calibrated.")
            return
        elif not self._calibration_packages_dict["pose"]:
            print("No image to use for pose.")
            return

        frame_gray, corners = self._calibration_packages_dict["pose"]
        corners2 = cv.cornerSubPix(
            frame_gray,
            corners,
            (11, 11),
            (-1, -1),
            constants.CRITERIA
        )
        checkerboard_3d_reference_points_array = self.get_checkerboard_3d_reference_points(use_checkerboard_thickness=True)
        try:
            current_camera.pose(
                checkerboard_3d_reference_points_array,
                corners2
            )
            self._overlay_need_update = True
        except Exception:
            traceback.print_exc()

    @QtCore.pyqtSlot()
    def uncalibrate(self):
        """Remove all calibration settings on the current camera."""
        current_camera = self.get_current_camera()
        if current_camera is not None:
            self.pause_ticker()
            current_camera.uncalibrate()
            for view_name in self._calibration_packages_dict.keys():
                self._calibration_packages_dict[view_name] = None
                push_button = getattr(self.ui, f"push_calibration_image_{view_name}")
                push_button.setText(view_name.capitalize())
                push_button.setIcon(QtGui.QIcon())
            self.start_ticker()
        self.set_enabled_for_calibrated_camera()

    def get_checkerboard_3d_reference_points(self, use_checkerboard_thickness=True):
        """Get checkboard 3D reference points.

        :param use_checkerboard_thickness: If set to True, will return checkerboard thickness for z values instead of 0.0. (True)
        :type use_checkerboard_thickness: bool

            .. note:: This should be set to False when calibrating and True when determining camera pose.

        :return: Array of reference points.
        :rtype: :class:`np.ndarray`
        """
        square_length = self.ui.double_length_of_square.value()
        checkerboard_thickness = self.ui.double_thickness.value()
        if self.ui.combo_units.currentText() == "Centimeters":
            square_length = common.cmToIn(square_length)
            checkerboard_thickness = common.cmToIn(checkerboard_thickness)

        dim_x = self.ui.spin_number_of_squares_w.value() - 1
        dim_x_2 = int(dim_x / 2)
        dim_y = self.ui.spin_number_of_squares_h.value() - 1
        dim_y_2 = int(dim_y / 2)

        checkerboard_ref_points = []

        for y in range(dim_y - 1, -1, -1):
            for x in range(dim_x):
                checkerboard_ref_points.append([
                    (x - dim_x_2) * square_length,
                    (y - dim_y_2) * square_length,
                    checkerboard_thickness if use_checkerboard_thickness else 0.0
                ])

        return np.array(checkerboard_ref_points, np.float32)

    @QtCore.pyqtSlot()
    def camera_save(self):
        """Save the current camera settings and calibration in the default calibration folder."""
        error_message = ""
        if (current_camera := self.get_current_camera()) is not None:
            try:
                filepath = current_camera.get_save_filepath()
                if os.path.exists(filepath):
                    answer = common.message_box(
                        title="Question",
                        text="File already exist, do you want to overwrite ?",
                        info_text=filepath,
                        icon_name="Question",
                        button_names_list=["Yes", "No"]
                    )
                    if answer != "Yes":
                        return
                current_camera.save(filepath)
                print(f"Current camera saved to : '{filepath}'")
            except Exception as err:
                error_message = str(err)

        else:
            error_message = "No current camera selected."

        if error_message:
            common.message_box(
                title="Error",
                text="Unable to save camera data.",
                info_text=error_message,
                icon_name="Critical",
                button_names_list=["Close"]
            )

    @QtCore.pyqtSlot()
    def camera_load(self):
        """Load saved camera settings and calibration data."""
        filepath_list = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', common.get_saved_subdir("camera"))

        if not filepath_list or not filepath_list[0]:
            return

        camera_data = common.load_camera_data(filepath_list[0])
        camera_data['debug'] = True
        device_id = camera_data['device_id']
        current_camera = self.get_current_camera()
        device_id_available = device_id in self.get_available_device_ids_list(as_list_of_str=False)
        replace_camera = False
        if current_camera is not None:
            info_text = "Answering 'Yes' will load the camera settings and calibration using the current camera device id."
            button_names_list = ["Yes", "Cancel"]

            if device_id_available:
                info_text += "<br>Answering 'No' will create a new camera with the device id stored in the file."
                button_names_list.insert(1, "No")

            answer = common.message_box(
                title="Load Camera Calibration",
                text="Replace current camera ?",
                info_text=info_text,
                icon_name="Question",
                button_names_list=button_names_list
            )
            if answer == "Cancel":
                return
            elif answer == "Yes":
                replace_camera = True

        self.pause_ticker()
        if replace_camera:
            current_camera.load(camera_data)
            self.start_ticker()
        else:
            # create the camera objects
            new_camera = camera.Camera(**camera_data)
            self._cameras_dict[device_id] = new_camera
            self._current_camera_id = device_id

            # add to list
            self.ui.list_cameras.addItem(f'Camera ID: {device_id}, "{new_camera.name}", "{new_camera.model_name}"')

            # select the new camera item in list
            self.ui.list_cameras.setCurrentRow(self.ui.list_cameras.count() - 1)

        self._overlay_need_update = True
        self.set_enabled_for_calibrated_camera()

    @QtCore.pyqtSlot(float)
    def update_table_transforms(self, _=0.0):
        """Update the table translation and rotation."""
        if self._disable_table_change:
            return

        self._table.set_transforms(
            self.ui.double_table_t_x.value(),
            self.ui.double_table_t_y.value(),
            self.ui.double_table_t_z.value(),
            self.ui.double_table_r_x.value(),
            self.ui.double_table_r_y.value(),
            self.ui.double_table_r_z.value(),
        )

        self._overlay_need_update = True

    @QtCore.pyqtSlot(int)
    def update_table_dimensions(self, _=0):
        """Update the table dimensions."""
        if self._disable_table_change:
            return

        self._table.set_dimensions(
            self.ui.spin_table_w.value(),
            self.ui.spin_table_h.value(),
        )

        self._overlay_need_update = True

    @QtCore.pyqtSlot(int)
    def update_table_border_color(self, _=0):
        """Update the table border color."""
        if self._disable_table_change:
            return

        self._table.set_border_color_from_name(
            self.ui.combo_table_border_color.currentText(),
            self.ui.spin_table_border_color_alpha.value(),
        )

        self._overlay_need_update = True

    @QtCore.pyqtSlot()
    def reset_table_transforms(self):
        """Reset the table transforms."""
        self._disable_table_change = True
        self.ui.double_table_t_x.setValue(0.0)
        self.ui.double_table_t_y.setValue(0.0)
        self.ui.double_table_t_z.setValue(0.0)
        self.ui.double_table_r_x.setValue(0.0)
        self.ui.double_table_r_y.setValue(0.0)
        self.ui.double_table_r_z.setValue(0.0)
        self._disable_table_change = False
        self.update_table_transforms()

    def update_axes_and_table_layer(self, width, height):
        """Update the axes and table layer to be composited on top of the image.

        :param width: Width of the overlay image.
        :type width: int

        :param height: Height of the overlay image.
        :type height: int
        """
        if (current_camera := self.get_current_camera()) is not None:

            # Prepare transparent overlay
            image_size = QtCore.QSize(width, height)
            self._image_overlay = QtGui.QImage(image_size, QtGui.QImage.Format.Format_ARGB32_Premultiplied)
            painter = QtGui.QPainter(self._image_overlay)
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode.CompositionMode_Source)
            painter.fillRect(self._image_overlay.rect(), QtCore.Qt.GlobalColor.transparent)

            square_length = self.ui.double_length_of_square.value()
            checkerboard_thickness = self.ui.double_thickness.value()
            if self.ui.combo_units.currentText() == "Centimeters":
                square_length = common.cmToIn(square_length)
                checkerboard_thickness = common.cmToIn(checkerboard_thickness)

            # Draw axes on the checkerboard for easy verification
            axes = np.float32(
                [
                    [0, 0, checkerboard_thickness],
                    [5.0 * square_length, 0, checkerboard_thickness],
                    [0, 5.0 * square_length, checkerboard_thickness],
                    [0, 0, 5.0 * square_length + checkerboard_thickness]
                ]
            ).reshape(-1, 3)
            projected_points = current_camera.project_points(axes, undistorted=True, as_integers=True)
            origin_x, origin_y = projected_points[0].ravel()
            x_axis_x, x_axis_y = projected_points[1].ravel()
            y_axis_x, y_axis_y = projected_points[2].ravel()
            z_axis_x, z_axis_y = projected_points[3].ravel()

            # Draw Axes
            brush = QtGui.QBrush()
            painter.setBrush(brush)
            pen = QtGui.QPen(QtCore.Qt.GlobalColor.red, 2, QtCore.Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawLine(origin_x, origin_y, x_axis_x, x_axis_y)
            pen.setColor(QtCore.Qt.GlobalColor.green)
            painter.setPen(pen)
            painter.drawLine(origin_x, origin_y, y_axis_x, y_axis_y)
            pen.setColor(QtCore.Qt.GlobalColor.blue)
            painter.setPen(pen)
            painter.drawLine(origin_x, origin_y, z_axis_x, z_axis_y)

            # table border
            table_corners_list = self._table.get_corners()
            projected_points = current_camera.project_points(table_corners_list, undistorted=True, as_integers=True)
            self._table_corner_points_list = [
                QtCore.QPointF(*projected_points[0].ravel()),
                QtCore.QPointF(*projected_points[1].ravel()),
                QtCore.QPointF(*projected_points[2].ravel()),
                QtCore.QPointF(*projected_points[3].ravel()),
                QtCore.QPointF(*projected_points[0].ravel()),
            ]
            pen.setColor(self._table.color)
            painter.setPen(pen)
            painter.drawPolyline(self._table_corner_points_list)

            painter.end()

            self._overlay_need_update = False

    def table_save(self):
        """Save the table to file."""
        filepath = self._table.get_save_filepath()
        if os.path.exists(filepath):
            answer = common.message_box(
                title="Question",
                text="File already exist, do you want to overwrite ?",
                info_text=filepath,
                icon_name="Question",
                button_names_list=["Yes", "No"]
            )
            if answer != "Yes":
                return
        self._table.save(filepath)

    def fill_table_settings(self):
        """Sync the table settings with the current table."""
        self._disable_table_change = True
        self.ui.edit_table_name.setText(self._table.name)
        width, height = self._table.get_dimensions()
        self.ui.spin_table_w.setValue(width)
        self.ui.spin_table_h.setValue(height)
        border_color_name, alpha = self._table.get_border_color_name_and_alpha()
        index = self.ui.combo_table_border_color.findText(border_color_name)
        if index > -1:
            self.ui.combo_table_border_color.setCurrentIndex(index)
        self.ui.spin_table_border_color_alpha.setValue(alpha)
        tx, ty, tz, rx, ry, rz = self._table.get_transforms()
        self.ui.double_table_t_x.setValue(tx)
        self.ui.double_table_t_y.setValue(ty)
        self.ui.double_table_t_z.setValue(tz)
        self.ui.double_table_r_x.setValue(rx)
        self.ui.double_table_r_y.setValue(ry)
        self.ui.double_table_r_z.setValue(rz)
        self._disable_table_change = False

    def table_load(self):
        """Load a table from file."""
        filepath_list = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', common.get_saved_subdir("table"))

        if not filepath_list or not filepath_list[0]:
            return

        with open(filepath_list[0], 'r') as fid:
            table_data = json.loads(fid.read())

        self._table.load(table_data)
        self.fill_table_settings()
        self._overlay_need_update = True

    @QtCore.pyqtSlot(str)
    def set_table_name(self, name):
        """Set the table name.

        :param name: New name for the table.
        :type name: str
        """
        self._table.name = name

    @QtCore.pyqtSlot()
    def snapshot_save(self):
        """Save the latest image to disk."""
        now = datetime.now()
        daystamp = now.strftime("%Y_%m_%d")
        timestamp = now.strftime("%Y_%m_%d_%H_%M_%S")
        name = re.sub("[^a-zA-Z0-9_]", "_", self.ui.edit_snapshot_name.text())
        snapshot_dir_path = common.get_saved_subdir('snapshot')
        if name:
            filepath = f"{snapshot_dir_path}/{name}/{name}__{timestamp}.png"
        else:
            filepath = f"{snapshot_dir_path}/{daystamp}/{timestamp}.png"

        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))

        self.latest_image.save(filepath)  # , quality=95)
        print(f"Snapshot saved to: '{filepath}'")

    def set_enabled_for_calibrated_camera(self):
        """Enable or disable widgets based on whether or not the current camera is calibrated."""
        current_camera = self.get_current_camera()
        is_calibrated = current_camera is not None and current_camera.is_calibrated()
        is_posed = current_camera is not None and current_camera.is_posed()
        num_calibration_images = sum([1 for _view_name in ['top', 'front', 'side'] if self._calibration_packages_dict[_view_name] is not None])
        self.ui.combo_camera_capture_resolution.setEnabled(not is_calibrated)
        self.ui.slider_camera_focus.setEnabled(not is_calibrated)
        self.ui.slider_camera_zoom.setEnabled(not is_calibrated)
        self.ui.push_calibrate.setEnabled(not is_calibrated and num_calibration_images == 3)
        self.ui.push_calibrate.setText("Calibrated" if is_calibrated else "Calibrate")
        self.ui.push_uncalibrate.setEnabled(is_calibrated)
        self.ui.push_pose.setEnabled(is_calibrated and self._calibration_packages_dict['pose'] is not None)
        self.ui.push_pose.setText("Posed" if is_posed else "Pose")
        self.ui.push_calibration_image_top.setEnabled(not is_calibrated)
        self.ui.push_calibration_image_front.setEnabled(not is_calibrated)
        self.ui.push_calibration_image_side.setEnabled(not is_calibrated)
        self.ui.push_calibration_image_pose.setEnabled(is_calibrated)
        self.ui.combo_camera_device_id.setEnabled(not is_calibrated)

    def _init_model_detection(self):
        """Initialize model detection."""
        print("Initializing the model detector...")
        try:
            self._model_dectector = model_detection.ModelDetector(
                trained_model_path=os.getenv('TRAINED_MODEL_DETECTION_PATH'),
                label_map_path=os.getenv('LABEL_MAP_PATH'),
            )
        except Exception:
            print("Failed to initialize model detector:")
            traceback.print_exc()
        else:
            print(f"Model detector initialized successfully. [{'Using' if self._model_dectector.is_using_gpu() else 'No'} GPU]")

    @QtCore.pyqtSlot()
    def _start_stop_model_detection(self):
        if self._model_dectector is None:
            self.ui.check_model_detection.setCheckState(QtCore.Qt.CheckState.Unchecked)
        elif self.ui.check_model_detection.isChecked():
            self._model_dectector.start()
        else:
            self._model_dectector.stop()
