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
"""This module contains everything related to text to speech."""

import subprocess
import pygame
import queue
import os
import mmap
import re

from PyQt6 import QtCore

from . import constants


def get_available_voices():
    """Get available voices on disk.

    :return: Voice names list.
    :rtype: list[str]
    """
    onnx_dict = {}
    json_list = []
    for _fd_name in os.listdir(constants.PIPER_VOICES_DIRPATH):
        filename, extension = os.path.splitext(_fd_name)
        if filename.startswith('en_'):
            if extension == ".json":
                json_list.append(filename)
            elif extension == ".onnx":
                onnx_dict[_fd_name] = filename

    return sorted([onnx_dict[_f] for _f in json_list if _f in onnx_dict])


class Narrator(QtCore.QThread):

    def __init__(self, voice=None):
        """Initialize.

        :param voice: Voice name. (None)
        :type voice: str

            **Example: 'en_US-kristin'**
        """
        super().__init__()
        pygame.init()
        pygame.mixer.init(frequency=22050)
        self._sound_num = 0
        self._q = queue.SimpleQueue()
        self._is_running = False
        self._voice = voice
        self._startupinfo = subprocess.STARTUPINFO()
        self._startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        self._startupinfo.wShowWindow = subprocess.SW_HIDE

    def speak(self, text, voice=None):
        """Add text and voice to queue.

        :param text: Text to say.
        :type text: str

        :param voice: Voice name override. (None)
        :type voice: str

            **Example: 'en_US-kristin'**
        """
        self._q.put(
            {
                'text': re.sub("[^0-9a-zA-Z!\\?\\.,;:\\- ']", " ", text.replace('"', "'")),
                'voice': voice if voice else self._voice
            }
        )

    def empty_queue(self):
        """Remove all items in the queue."""
        while not self._q.empty():
            self._q.get(block=False)

    def set_voice(self, voice):
        """Set the default voice.

        :param voice: Voice name.
        :type voice: str

            **Example: 'en_US-kristin'**
        """
        self._voice = voice

    def is_running(self):
        """Whether or not narrator is actively waiting for text to say.

        :return: If narrator is running.
        :rtype: bool
        """
        return self._is_running

    def stop(self):
        """Stop this narrator."""
        self._is_running = False
        self.empty_queue()

    def run(self):
        """Speak queue items."""

        self._is_running = True
        while self._is_running:
            try:
                item = self._q.get(timeout=2)
            except queue.Empty:
                continue

            if not self._is_running:
                break
            if not item['voice']:
                continue

            self._sound_num = (self._sound_num + 1) % 2
            output_file = constants.VOICE_NARRATOR_TEMP_OUTPUT_FILEPATH_TEMPLATE.format(self._sound_num)
            command_str = f"echo \"{item['text']}\" | {constants.PIPER_EXECUTABLE} -q -m {constants.PIPER_VOICES_DIRPATH}\\{item['voice']}.onnx -f {output_file}"
            subprocess.check_output(command_str, shell=True, startupinfo=self._startupinfo)
            if os.path.exists(output_file):
                with open(output_file) as f:
                    sound_data = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                pygame.mixer.music.load(sound_data)
                pygame.mixer.music.play()

                # wait_till_over:
                while pygame.mixer.music.get_busy() and self._is_running:
                    pygame.time.Clock().tick(10)
                pygame.mixer.music.stop()
            else:
                print(f"ERROR: Unable to play '{output_file}', there must have been a error with the following command:\n>>> {command_str}.")
