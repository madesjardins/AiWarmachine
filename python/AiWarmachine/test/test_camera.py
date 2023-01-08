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
"""Camera test script.

Simply execute and press start test camera.
Make sure the python folder was added to the path environment variable before running.
"""
import sys
import os
import time

from PyQt6 import QtWidgets, QtCore, QtGui, uic
import cv2 as cv

from AiWarmachine import camera as aiw_camera
from AiWarmachine import common as aiw_common


class MyTicker(QtCore.QThread):

    tick = QtCore.pyqtSignal(float)

    def __init__(self, fps):
        super().__init__()
        self.time_interval = 1.0 / fps
        self.is_running = False
        self.play_time = 0.0

    def run(self):
        self.is_running = True
        self.play_time = 0.0
        while self.is_running:
            self.tick.emit(self.play_time)
            time.sleep(self.time_interval)
            self.play_time += self.time_interval

    def stop(self):
        self.is_running = False


class MyDialog(QtWidgets.QDialog):

    def __init__(self, parent=None):

        super().__init__(parent=parent)
        self._animation_frame = 0
        self.ui = uic.loadUi(os.path.join(os.path.dirname(__file__), "test_camera.ui"))
        self.setWindowTitle("Camera Test")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.ui)
        self.setLayout(layout)

        self.ui.push_start.clicked.connect(self.start_camera)
        self.ui.push_pause.clicked.connect(self.pause_camera)
        self.ui.push_quit.clicked.connect(self.close)
        self.ui.spin_device_id.valueChanged.connect(self.change_device_id)
        self.ui.combo_resolution.currentTextChanged.connect(self.change_resolution)
        self.ui.spin_exposure.valueChanged.connect(self.change_exposure)
        self.ui.spin_focus.valueChanged.connect(self.change_focus)

        self.camera = aiw_camera.Camera(
            "Test",
            device_id=0,
            debug=True
        )
        self.ticker = MyTicker(60.0)
        self.ticker.tick.connect(self.tick)
        self.show()

    @QtCore.pyqtSlot(float)
    def tick(self, tick_time):
        camera_frame = self.camera.get_frame(show_info=True)
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
        if self.ui.check_actual_frame_size.isChecked():
            self.ui.label_image.resize(image.width(), image.height())
        else:
            image = image.scaledToWidth(self.ui.scroll_image.size().width() - 20)
        self.ui.label_image.setPixmap(QtGui.QPixmap.fromImage(image))

    @QtCore.pyqtSlot()
    def start_camera(self):
        self.ticker.stop()
        self.ticker.wait()
        self.camera.start()
        self.ticker.start()

    @QtCore.pyqtSlot()
    def pause_camera(self):
        self.ticker.stop()
        self.ticker.wait()
        self.camera.stop()

    @QtCore.pyqtSlot()
    def close(self):
        self.ticker.stop()
        self.ticker.wait()
        self.camera.release()
        super().close()

    @QtCore.pyqtSlot(int)
    def change_device_id(self, device_id):
        self.camera.device_id = device_id
        self.start_camera()

    @QtCore.pyqtSlot(str)
    def change_resolution(self, resolution_text):
        was_running = self.camera.is_running()
        width_str, height_str = resolution_text.split("x")
        if was_running:
            self.camera.stop()
        self.camera.set_capture_property(cv.CAP_PROP_FRAME_WIDTH, int(width_str))
        self.camera.set_capture_property(cv.CAP_PROP_FRAME_HEIGHT, int(height_str))
        if was_running:
            self.camera.start()

    @QtCore.pyqtSlot(int)
    def change_exposure(self, exposure):
        self.camera.set_capture_property(cv.CAP_PROP_EXPOSURE, exposure)

    @QtCore.pyqtSlot(int)
    def change_focus(self, focus):
        self.camera.set_capture_property(cv.CAP_PROP_FOCUS, focus)


app = QtWidgets.QApplication(sys.argv)
my_dial = MyDialog()
app.exec()
