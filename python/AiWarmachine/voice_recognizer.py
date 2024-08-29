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
"""The game table class contains everything related to the table, like play area dimension."""

import sys
import queue
from ast import literal_eval

from PyQt6 import QtCore
import sounddevice as sd
from vosk import Model, KaldiRecognizer


def query_devices():
    """Get available audio devices.

    :return: A dictionary of device IDs and their names.
    :rtype: dict[int: str]
    """
    data = {}
    for _device in sd.query_devices():
        if _device['max_input_channels']:
            try:
                sd.query_devices(_device['index'], "input")
                data[_device['index']] = _device['name']
            except Exception:
                continue
    return data


class VoiceRecognizer(QtCore.QThread):

    text_partial_result = QtCore.pyqtSignal(str)
    text_result = QtCore.pyqtSignal(str)

    def __init__(self, device_id=0):
        """Initializer.

        :param device_id: The audio input device_id. (0)
        :type device_id: int
        """
        super().__init__()
        self._device_id = device_id
        self._model = Model(lang="en-us")
        self._is_running = False

    def stop(self):
        """Stop the thread from running."""
        self._is_running = False

    def set_device_id(self, device_id):
        """Set the device id.

        .. note:: In order for this to be applied, you need to restart the thread.

        :param device_id: The audio input device_id.
        :type device_id: int
        """
        self._device_id = device_id

    def is_running(self):
        """Whether or not the voice recognizer is running.

        :return: Is the voice recognizer running.
        :rtype: bool
        """
        return self._is_running

    def _callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        self._queue.put(bytes(indata))

    def run(self):
        """Start listening"""
        self._queue = queue.Queue()
        device_info = sd.query_devices(self._device_id, "input")
        samplerate = int(device_info["default_samplerate"])
        self._is_running = True
        with sd.RawInputStream(
            samplerate=samplerate,
            blocksize=8000,
            device=self._device_id,
            dtype="int16",
            channels=1,
            callback=self._callback
        ):
            rec = KaldiRecognizer(self._model, samplerate)
            while self._is_running:
                data = self._queue.get()
                if rec.AcceptWaveform(data):
                    result_dict = literal_eval(rec.Result()) or {}
                    text = result_dict.get('text', "").strip()
                    if text in ["huh", "hum", "ah", "ha"]:
                        continue
                    elif text:
                        self.text_result.emit(f"{text.capitalize()}.")
                else:
                    result_dict = literal_eval(rec.PartialResult()) or {}
                    text = result_dict.get('partial', "").strip()
                    if text:
                        self.text_partial_result.emit(text)
