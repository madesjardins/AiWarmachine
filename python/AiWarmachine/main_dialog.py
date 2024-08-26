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
"""Main dialog to setup your cameras and table."""

import os
import traceback
import re
from functools import partial
from datetime import datetime
import time

from PyQt6 import QtWidgets, QtCore, QtGui, uic
import cv2 as cv

from . import common, constants, viewport_label, projector_dialog


class MainDialog(QtWidgets.QDialog):
    """Main dialog."""

    def __init__(self, core, parent=None):
        """Initialize.

        :param core: The main core.
        :type core: :class:`MainCore`

        :param parent: The parent widget. (None)
        :type parent: :class:`QWidget`
        """
        super().__init__(parent=parent)

        self.core = core
        self._disable_camera_settings_change = False
        self._in_calibration = False
        self._previous_time = time.time()
        self._selected_corner_index = None
        self._selected_corner_offset = QtCore.QPoint(0, 0)

        self._init_ui()
        self._init_connections()
        self._init_game_table()
        self.show()

    def _init_ui(self):
        """Initialize the UI."""
        self.ui = uic.loadUi(os.path.join(os.path.dirname(__file__), "ui", "main_widget.ui"))
        self.setWindowTitle("Calibration")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.ui)
        self.setLayout(layout)

        # Label for viewport
        self.ui.label_viewport_image = viewport_label.ViewportLabel(self.ui.scroll_viewport_widget)
        self.ui.scroll_viewport_widget.layout().addWidget(self.ui.label_viewport_image)

        self.fill_current_camera_settings(default=True)
        self.set_enabled_for_calibrations()

        if constants.IS_LINUX:
            self.ui.slider_camera_focus.hide()
            self.ui.label_camera_focus.hide()
            self.ui.spin_camera_exposure.setRange(3, 2047)
            self.ui.spin_camera_exposure.setSingleStep(25)
            self.ui.spin_camera_exposure.setValue(250)

        self.table_corners_widgets_dict = {
            "camera": [
                (self.ui.spin_table_camera_corner_bl_x, self.ui.spin_table_camera_corner_bl_y),
                (self.ui.spin_table_camera_corner_tl_x, self.ui.spin_table_camera_corner_tl_y),
                (self.ui.spin_table_camera_corner_tr_x, self.ui.spin_table_camera_corner_tr_y),
                (self.ui.spin_table_camera_corner_br_x, self.ui.spin_table_camera_corner_br_y)
            ],
            "projector": [
                (self.ui.spin_table_projector_corner_bl_x, self.ui.spin_table_projector_corner_bl_y),
                (self.ui.spin_table_projector_corner_tl_x, self.ui.spin_table_projector_corner_tl_y),
                (self.ui.spin_table_projector_corner_tr_x, self.ui.spin_table_projector_corner_tr_y),
                (self.ui.spin_table_projector_corner_br_x, self.ui.spin_table_projector_corner_br_y)
            ]
        }

        self.launch_projector_dialog()

    def _init_connections(self):
        """Initialize connections."""
        # General events
        self.ui.push_quit.clicked.connect(self.close)
        self.ui.label_viewport_image.key_press_event.connect(self.key_pressed)

        # Cameras list
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

        # Camera Calibration
        self.ui.push_calibration_image_top.clicked.connect(partial(self.trigger_calibration_image, "top"))
        self.ui.push_calibration_image_front.clicked.connect(partial(self.trigger_calibration_image, "front"))
        self.ui.push_calibration_image_side.clicked.connect(partial(self.trigger_calibration_image, "side"))
        self.ui.push_camera_calibrate.clicked.connect(self.calibrate)
        self.ui.push_camera_uncalibrate.clicked.connect(self.uncalibrate)

        # Snapshot
        self.ui.push_snapshot_save.clicked.connect(self.snapshot_save)

        # Tick
        self.core.refresh_ticker.timeout.connect(self.tick)
        self.ui.spin_viewport_refresh_rate.valueChanged.connect(self.core.set_refresh_ticker_rate)
        self.ui.double_safe_image_grab_coefficient.valueChanged.connect(self.core.set_safe_image_grab_coefficient)
        self.ui.spin_qr_detection_rate.valueChanged.connect(self.core.set_qr_detection_ticker_rate)

        self.ui.push_reset_qr_detections.clicked.connect(self.core.qr_detector.reset)

    def launch_projector_dialog(self):
        """Pop the projector dialog, connect ticker and start."""
        self.projector_dialog = projector_dialog.ProjectorDialog(core=self.core, main_dialog=self)
        self.core.projector_ticker.timeout.connect(self.projector_dialog.tick)
        self.ui.spin_projector_refresh_rate.valueChanged.connect(self.core.set_projector_ticker_rate)
        self.core.projector_ticker.start()

    # #############################################
    #
    # GENERAL EVENTS
    #
    # #############################################
    @QtCore.pyqtSlot(QtGui.QCloseEvent)
    def closeEvent(self, a0):
        """Stop ticker and release all cameras."""
        try:
            self.core.stop_all()
            self.projector_dialog.close()
        except Exception:
            traceback.print_exc()
        return super().closeEvent(a0)

    @QtCore.pyqtSlot()
    def close(self):
        """Close dialog."""
        return super().close()

    @QtCore.pyqtSlot(str)
    def key_pressed(self, key_text):
        """A key was pressed.

        :param key_text: The text value of the key.
        :type key_text: str
        """
        # Set Display actual resolution
        if key_text == "f":
            if self.ui.check_display_actual_resolution.isChecked():
                self.ui.check_display_actual_resolution.setCheckState(QtCore.Qt.CheckState.Unchecked)
            else:
                self.ui.check_display_actual_resolution.setCheckState(QtCore.Qt.CheckState.Checked)

        # Move by 1 pixel selected corner ['w', 'a', 's', 'd']
        if key_text in constants.MOVE_KEY_POINTS_DICT and self._selected_corner_index is not None:
            width = self.latest_image.width()
            height = self.latest_image.height()
            corner_points_list = self.core.game_table.get_in_camera_corners_as_points()
            self.table_corners_widgets_dict['camera'][self._selected_corner_index][constants.TABLE_CORNERS_AXIS_X].setValue(
                min(max(0, corner_points_list[self._selected_corner_index].x() + constants.MOVE_KEY_POINTS_DICT[key_text].x()), width - 1)
            )
            self.table_corners_widgets_dict['camera'][self._selected_corner_index][constants.TABLE_CORNERS_AXIS_Y].setValue(
                min(max(0, corner_points_list[self._selected_corner_index].y() + constants.MOVE_KEY_POINTS_DICT[key_text].y()), height - 1)
            )

    def set_enabled_for_calibrations(self):
        """Set enabled/disabled on different widget based on calibrated status."""
        self.set_enabled_for_calibrated_camera()
        self.set_enabled_for_calibrated_table()

    # #############################################
    #
    # REFRESH VIEWPORT
    #
    # #############################################
    def start_refresh_ticker(self):
        """Start the ticker."""
        self.core.refresh_ticker.stop()
        self.core.refresh_ticker.start()

    def pause_refresh_ticker(self):
        """Stop the ticker."""
        self.core.refresh_ticker.stop()

    @QtCore.pyqtSlot()
    def tick(self):
        """Refresh viewport."""
        if self._in_calibration:
            image, info_str = self.core.get_image(
                in_calibration=self._in_calibration,
                number_of_squares_w=self.ui.spin_number_of_squares_w.value(),
                number_of_squares_h=self.ui.spin_number_of_squares_h.value()
            )
        else:
            image, info_str = self.core.get_image()

        if image is None:
            return

        if info_str is not None:
            self.ui.edit_camera_effective_resolution.setText(info_str)

        self.latest_image = image

        # Table corners overlay
        current_camera = self.core.camera_manager.get_camera()
        is_calibrated = current_camera is not None and current_camera.is_calibrated()
        if is_calibrated and info_str is not None:
            corners_overlay, corners_overlay_roi = self.core.game_table.get_camera_corners_overlay()
            if corners_overlay is not None:
                image = common.composite_images(image, corners_overlay, corners_overlay_roi[0], corners_overlay_roi[1])

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

    # #############################################
    #
    # CAMERA SETTINGS
    #
    # #############################################
    def set_enabled_for_calibrated_camera(self):
        """Enable or disable widgets based on whether or not the current camera is calibrated."""
        current_camera = self.core.camera_manager.get_camera()
        is_calibrated = current_camera is not None and current_camera.is_calibrated()
        has_all_calibration_images = self.core.camera_calibration_helper.has_all_calibration_images()
        self.ui.combo_camera_capture_resolution.setEnabled(not is_calibrated)
        self.ui.slider_camera_focus.setEnabled(not is_calibrated)
        self.ui.slider_camera_zoom.setEnabled(not is_calibrated)
        self.ui.push_camera_calibrate.setEnabled(not is_calibrated and has_all_calibration_images)
        self.ui.push_camera_calibrate.setText("Calibrated" if is_calibrated else "Calibrate")
        self.ui.push_camera_uncalibrate.setEnabled(is_calibrated)
        self.ui.push_calibration_image_top.setEnabled(not is_calibrated)
        self.ui.push_calibration_image_front.setEnabled(not is_calibrated)
        self.ui.push_calibration_image_side.setEnabled(not is_calibrated)
        self.ui.combo_camera_device_id.setEnabled(not is_calibrated)

    @QtCore.pyqtSlot(QtWidgets.QSlider, int)
    def reset_camera_slider(self, slider, default_value):
        """Reset the slider to its default value..

        :param slider: The slider to reset.
        :type slider: :class:`QSlider`

        :param default_value: The default value.
        :type default_value: int
        """
        slider.setValue(default_value)

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

    def get_current_camera_item(self):
        """Get the current camera item if any.

        :return: The camera item.
        :rtype: :class:`QListWidgetItem`
        """
        if selected_items := self.ui.list_cameras.selectedItems():
            return selected_items[0]
        return None

    @QtCore.pyqtSlot()
    def set_viewport_to_selected(self):
        """Set the viewport to the selected camera in the list."""
        self.pause_refresh_ticker()
        if (device_id := self.get_selected_device_id()) is not None:
            if self.core.camera_manager.set_current_camera(device_id):
                self.start_refresh_ticker()
                self.fill_current_camera_settings()

            self.ui.push_delete_camera.setEnabled(True)
        else:
            self.ui.push_delete_camera.setEnabled(False)
        self.set_enabled_for_calibrations()

    @QtCore.pyqtSlot()
    def add_camera(self):
        """Add a new camera to the list."""
        available_device_ids_list = self.core.camera_manager.get_available_device_ids_list(as_list_of_str=True)
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
        new_camera = self.core.camera_manager.add_camera(device_id=device_id)

        # add to list
        self.ui.list_cameras.addItem(f'Camera ID: {device_id}, "{new_camera.name}", "{new_camera.model_name}"')

        # select the new camera item in list
        self.ui.list_cameras.setCurrentRow(self.ui.list_cameras.count() - 1)

    @QtCore.pyqtSlot()
    def delete_camera(self):
        """Delete the selected camera."""
        try:
            self.pause_refresh_ticker()
            if (device_id := self.get_selected_device_id()) is not None:
                self.core.camera_manager.delete_camera(device_id)
                self.ui.list_cameras.takeItem(self.ui.list_cameras.currentRow())
        except Exception:
            traceback.print_exc()
        self.set_enabled_for_calibrations()

    def fill_current_camera_settings(self, default=False):
        """Fill current camera settings fields.

        :param default: If set to True, will fill the fields using default values. (False)
        :type default: bool
        """
        self._disable_camera_settings_change = True

        if default:
            self.ui.edit_camera_name.setText("")
            self.ui.combo_camera_device_id.clear()
            self.ui.combo_camera_device_id.addItems(self.core.camera_manager.get_available_device_ids_list(as_list_of_str=True))
            self.ui.edit_camera_model_name.setText("")

        elif (current_camera := self.core.camera_manager.get_camera()) is not None:
            self.ui.edit_camera_name.setText(current_camera.name)
            self.ui.edit_camera_model_name.setText(current_camera.model_name)
            device_id_str = str(current_camera.device_id)
            available_device_ids_list = sorted(set(self.core.camera_manager.get_available_device_ids_list(as_list_of_str=True) + [device_id_str]))
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

    @QtCore.pyqtSlot(str)
    def set_camera_capture_resolution(self, resolution_str):
        """Set the current camera capture resolution.

        :param resolution_str: Resolution as a str '{width}x{height}'.
        :type resolution_str: str
        """
        if self._disable_camera_settings_change:
            return
        width_str, height_str = resolution_str.split("x")
        self.pause_refresh_ticker()
        self.core.camera_manager.set_current_camera_capture_resolution(int(width_str), int(height_str))
        self.start_refresh_ticker()

    @QtCore.pyqtSlot(int, int)
    def set_camera_prop_value(self, property_id, value):
        """Set the current camera property value.

        :param property_id: The cv.CAM_PROP_ value for this property.
        :type property_id: int

        :param value: The value.
        :type value: int
        """
        if self._disable_camera_settings_change:
            return
        self.core.camera_manager.set_current_camera_prop_value(property_id, value)

    def update_current_camera_item_label(self):
        """Update the current camera item's label."""
        if (
            (current_camera := self.core.camera_manager.get_camera()) is not None and
            (camera_item := self.get_current_camera_item()) is not None
        ):
            camera_item.setText(f'Camera ID: {current_camera.device_id}, "{current_camera.name}", "{current_camera.model_name}"')

    @QtCore.pyqtSlot(str)
    def set_current_camera_name(self, name):
        """Set the current camera name.

        :param name: The camera name.
        :type name: str
        """
        if self._disable_camera_settings_change:
            return
        if self.core.camera_manager.set_current_camera_name(name):
            self.update_current_camera_item_label()

    @QtCore.pyqtSlot(str)
    def set_current_camera_model_name(self, model_name):
        """Set the current camera model name.

        :param model_name: The camera model name.
        :type name: str
        """
        if self._disable_camera_settings_change:
            return
        if self.core.camera_manager.set_current_camera_model_name(model_name):
            self.update_current_camera_item_label()

    @QtCore.pyqtSlot()
    def camera_save(self):
        """Save the current camera settings and calibration in the default calibration folder."""
        error_message = ""
        if (current_camera := self.core.camera_manager.get_camera()) is not None:
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
        camera_data['debug'] = False
        device_id = camera_data['device_id']
        current_camera = self.core.camera_manager.get_camera()
        device_id_available = device_id in self.core.camera_manager.get_available_device_ids_list(as_list_of_str=False)
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

        self.pause_refresh_ticker()
        if replace_camera:
            current_camera.load(camera_data)
            self.start_refresh_ticker()
        else:
            # create the camera objects
            new_camera = self.core.camera_manager.add_camera(**camera_data)

            # add to list
            self.ui.list_cameras.addItem(f'Camera ID: {device_id}, "{new_camera.name}", "{new_camera.model_name}"')

            # select the new camera item in list
            self.ui.list_cameras.setCurrentRow(self.ui.list_cameras.count() - 1)

        self.set_enabled_for_calibrations()

    @QtCore.pyqtSlot(str)
    def set_current_camera_device_id(self, device_id_str):
        """Set the device id of the current camera to this value.

        :param device_id_str: The device id as a str.
        :type device_id_str: str
        """
        if self._disable_camera_settings_change:
            return
        device_id = int(device_id_str)
        self.pause_refresh_ticker()
        if self.core.camera_manager.set_current_camera_device_id(device_id):
            self.update_current_camera_item_label()
        if self.core.camera_manager.get_camera() is not None:
            self.start_refresh_ticker()

    # #############################################
    #
    # CAMERA CALIBRATION
    #
    # #############################################
    @QtCore.pyqtSlot()
    def calibrate(self):
        """Calibrate the camera using the top, front and side views."""
        current_camera = self.core.camera_manager.get_camera()
        if current_camera is None:
            print("No current camera")
            return
        try:
            mean_error = self.core.camera_calibration_helper.calibrate(
                camera=current_camera,
                number_of_squares_w=self.ui.spin_number_of_squares_w.value(),
                number_of_squares_h=self.ui.spin_number_of_squares_h.value()
            )
            print(f"Calibration error: {mean_error}")
        except Exception:
            traceback.print_exc()

        self.set_enabled_for_calibrations()

    @QtCore.pyqtSlot()
    def uncalibrate(self):
        """Remove all calibration settings on the current camera."""
        current_camera = self.core.camera_manager.get_camera()
        if current_camera is not None:
            self.pause_refresh_ticker()
            self.core.camera_calibration_helper.uncalibrate(current_camera)
            for view_name in self.core.camera_calibration_helper.get_view_names():
                push_button = getattr(self.ui, f"push_calibration_image_{view_name}")
                push_button.setText(view_name.capitalize())
                push_button.setIcon(QtGui.QIcon())
            self.start_refresh_ticker()
        self.set_enabled_for_calibrations()

    @QtCore.pyqtSlot(str)
    def trigger_calibration_image(self, view_name):
        """Trigger the countdown to take a calibration image.

        :param view_name: The name of the view, choices are: ['top', 'front', 'side'].
        :type view_name: str
        """
        self._in_calibration = True
        QtCore.QTimer.singleShot(3000, partial(self.set_calibration_image, view_name))

    @QtCore.pyqtSlot(str)
    def set_calibration_image(self, view_name):
        """Set a calibration image.

        :param view_name: The name of the view, choices are: ['top', 'front', 'side'].
        :type view_name: str
        """
        self._in_calibration = False
        if self.core.camera_calibration_helper.set_package(view_name):
            push_button = getattr(self.ui, f"push_calibration_image_{view_name}")
            push_button.setText("")
            image = self.core.camera_calibration_helper.get_package_image(view_name)
            pix = QtGui.QPixmap.fromImage(
                image.scaled(
                    push_button.width() - 10,
                    push_button.height() - 10,
                    aspectRatioMode=QtCore.Qt.AspectRatioMode.KeepAspectRatio
                )
            )
            push_button.setIcon(QtGui.QIcon(pix))
            push_button.setIconSize(pix.rect().size())

        self.set_enabled_for_calibrations()

    # #############################################
    #
    # SNAPSHOT
    #
    # #############################################
    @QtCore.pyqtSlot()
    def snapshot_save(self):
        """Save the latest image to disk."""
        if self.latest_image is not None:
            now = datetime.now()
            daystamp = now.strftime("%Y_%m_%d")
            timestamp = now.strftime("%Y_%m_%d_%H_%M_%S")
            folder_name = re.sub("[^a-zA-Z0-9_]", "_", self.ui.edit_snapshot_folder_name.text().strip())
            snapshot_name = re.sub("[^a-zA-Z0-9_]", "_", self.ui.edit_snapshot_name.text().strip())
            snapshot_dir_path = common.get_saved_subdir('snapshot')
            add_timestamp_to_snapshot = self.ui.check_add_timestamp_to_snapshot.isChecked()

            if folder_name:
                dir_path = f"{snapshot_dir_path}/{folder_name}"
            else:
                dir_path = f"{snapshot_dir_path}/{daystamp}"

            if snapshot_name:
                file_name = snapshot_name
            elif folder_name:
                file_name = folder_name
            else:
                file_name = timestamp

            if add_timestamp_to_snapshot and (snapshot_name or folder_name):
                file_name += f"__{timestamp}"

            file_path = f"{dir_path}/{file_name}.png"

            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))

            self.latest_image.save(file_path)
            print(f"Snapshot saved to: '{file_path}'")
        else:
            print("No image to save.")

    # #############################################
    #
    # Game table

    # #############################################
    def _init_game_table(self, do_connections=True):
        """Initialize game table values based on UI values and connections.

        :param do_connections: Whether or not to connect widget signals to gametable slot. (True)
        :type do_connections: bool
        """
        if do_connections:
            self.ui.label_viewport_image.mouse_press_event.connect(partial(self.update_table_camera_corners, True))
            self.ui.label_viewport_image.mouse_drag_event.connect(partial(self.update_table_camera_corners, False))
            self.ui.edit_table_name.textChanged.connect(self.core.game_table.set_name)
            self.ui.double_table_w.valueChanged.connect(self.core.game_table.set_width)
            self.ui.double_table_h.valueChanged.connect(self.core.game_table.set_height)
            self.ui.push_table_save.clicked.connect(self.table_save)
            self.ui.push_table_load.clicked.connect(self.table_load)
            self.ui.spin_table_resolution_factor.valueChanged.connect(self.core.game_table.set_resolution_factor)
            self.ui.push_table_calibrate.clicked.connect(self.calibrate_table)
            self.ui.push_table_uncalibrate.clicked.connect(self.uncalibrate_table)

        self.core.game_table.set_name(self.ui.edit_table_name.text())
        self.core.game_table.set_width(self.ui.double_table_w.value())
        self.core.game_table.set_height(self.ui.double_table_h.value())

        for corner_type_name, corner_type_index in constants.TABLE_CORNERS_TYPE_NAME_TO_INDEX.items():
            for corner_name, corner_index in constants.TABLE_CORNERS_NAME_TO_INDEX.items():
                for axis_name, axis_index in constants.TABLE_CORNERS_AXIS_NAME_TO_INDEX.items():
                    widget = getattr(self.ui, f"spin_table_{corner_type_name}_corner_{corner_name}_{axis_name}")
                    self.core.game_table.set_corner_position(
                        corner_type=corner_type_index,
                        corner_index=corner_index,
                        axis=axis_index,
                        value=widget.value(),
                    )
                    if do_connections:
                        widget.valueChanged.connect(partial(self.core.game_table.set_corner_position, corner_type_index, corner_index, axis_index))

        self.set_enabled_for_calibrations()

    def set_enabled_for_calibrated_table(self):
        """Enable or disable widgets based on whether or not the current table is calibrated."""
        current_camera = self.core.camera_manager.get_camera()
        camera_is_calibrated = current_camera is not None and current_camera.is_calibrated()
        is_calibrated = self.core.game_table.is_calibrated()
        self.ui.push_table_calibrate.setEnabled(not is_calibrated and camera_is_calibrated)
        self.ui.push_table_calibrate.setText("Calibrated" if is_calibrated else "Calibrate")
        self.ui.push_table_uncalibrate.setEnabled(is_calibrated)
        self.ui.double_table_w.setEnabled(not is_calibrated)
        self.ui.double_table_h.setEnabled(not is_calibrated)
        self.ui.spin_table_resolution_factor.setEnabled(not is_calibrated)
        self.ui.push_table_save.setEnabled(is_calibrated)
        self.ui.push_table_load.setEnabled(camera_is_calibrated)

    @QtCore.pyqtSlot()
    def calibrate_table(self):
        """Calculate perspective transforms for camera -> game and game->projector."""
        self.core.game_table.calibrate()
        self.set_enabled_for_calibrations()

    @QtCore.pyqtSlot()
    def uncalibrate_table(self):
        """Reset prespective transforms on game table."""
        self.core.game_table.uncalibrate()
        self.set_enabled_for_calibrations()

    @QtCore.pyqtSlot()
    def table_save(self):
        """Save the table to file."""
        filepath = self.core.game_table.get_save_filepath()
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
        self.core.game_table.save(filepath)
        print(f"Table successfully saved here: '{filepath}'.")

    def fill_table_settings(self):
        """Sync the table settings with the current table."""
        self.core.game_table.disable_slots = True

        table_data = self.core.game_table.get_data()
        self.ui.edit_table_name.setText(table_data['name'])
        self.ui.double_table_w.setValue(table_data['width'])
        self.ui.double_table_h.setValue(table_data['height'])
        self.ui.spin_table_resolution_factor.setValue(table_data['resolution_factor'])
        for corner_index in constants.TABLE_CORNERS_DRAWING_ORDER:
            self.table_corners_widgets_dict['camera'][corner_index][constants.TABLE_CORNERS_AXIS_X].setValue(table_data['in_camera_corners'][corner_index][constants.TABLE_CORNERS_AXIS_X])
            self.table_corners_widgets_dict['camera'][corner_index][constants.TABLE_CORNERS_AXIS_Y].setValue(table_data['in_camera_corners'][corner_index][constants.TABLE_CORNERS_AXIS_Y])
            self.table_corners_widgets_dict['projector'][corner_index][constants.TABLE_CORNERS_AXIS_X].setValue(table_data['in_projector_corners'][corner_index][constants.TABLE_CORNERS_AXIS_X])
            self.table_corners_widgets_dict['projector'][corner_index][constants.TABLE_CORNERS_AXIS_Y].setValue(table_data['in_projector_corners'][corner_index][constants.TABLE_CORNERS_AXIS_Y])

        self.core.game_table.disable_slots = False

    @QtCore.pyqtSlot()
    def table_load(self):
        """Load a table from file."""
        filepath_list = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', common.get_saved_subdir("table"))

        if not filepath_list or not filepath_list[0]:
            return

        self.core.game_table.load(filepath_list[0])
        self.fill_table_settings()
        self.set_enabled_for_calibrations()

    @QtCore.pyqtSlot(bool, float, float)
    def update_table_camera_corners(self, is_press, norm_pos_x, norm_pos_y):
        """Update table corners values.

        :param is_press: Whether this is a press event instead of a drag.
        :type is_press: bool
        """
        current_camera = self.core.camera_manager.get_camera()
        if current_camera is None or not current_camera.is_calibrated() or self.core.game_table.is_calibrated():
            return

        width = self.latest_image.width()
        height = self.latest_image.height()

        if is_press:
            corner_points_list = self.core.game_table.get_in_camera_corners_as_points()
            pos_mouse = QtCore.QPoint(int(norm_pos_x * width), int(norm_pos_y * height))

            self._selected_corner_index = None
            closest_corner_index = None
            closest_distance = None

            for corner_index in constants.TABLE_CORNERS_DRAWING_ORDER:
                test_pos = corner_points_list[corner_index] - pos_mouse
                test_distance = test_pos.manhattanLength()
                if (
                    test_distance < constants.MAXIMUM_CLOSEST_TABLE_CORNERS_DISTANCE and
                    (
                        closest_distance is None or
                        test_distance < closest_distance
                    )
                ):
                    closest_corner_index = corner_index
                    closest_distance = test_distance

            if closest_corner_index is not None:
                self._selected_corner_index = closest_corner_index
                self._selected_corner_offset = corner_points_list[closest_corner_index] - pos_mouse

        elif self._selected_corner_index is not None:
            pos_x = min(max(0, int(norm_pos_x * width) + self._selected_corner_offset.x()), width - 1)
            pos_y = min(max(0, int(norm_pos_y * height) + self._selected_corner_offset.y()), height - 1)

            self.table_corners_widgets_dict['camera'][self._selected_corner_index][constants.TABLE_CORNERS_AXIS_X].setValue(pos_x)
            self.table_corners_widgets_dict['camera'][self._selected_corner_index][constants.TABLE_CORNERS_AXIS_Y].setValue(pos_y)

            self.core.game_table.set_camera_corners_overlay_needs_update()
