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
"""Core module for the Warmachine title."""

import os
import re
import traceback
from typing import Optional

from PyQt6 import QtCore

from . import states, events, constants, model_info_database as midb
from importlib import reload
reload(states)
reload(events)
reload(constants)
reload(midb)

DATABASE_COMBO_CHOOSE_TEXT = "-- Choose a database --"


class TitleCore(QtCore.QObject):
    """Core class behind the title dialog."""

    refresh_armies = QtCore.pyqtSignal()

    def __init__(self, main_core):
        """Initialize.

        :param main_core: Main core.
        :type main_core: :class:`MainCore`
        """
        super().__init__()

        self.main_core = main_core
        self.transcript_lines = []
        self.current_title_state = states.TitleState.MENU
        self._model_databases_dict = {}
        self._current_model_database = None
        self._armies = [[], []]

        # voice recognizer
        self.main_core.voice_recognizer.text_result.connect(self.voice_event)

        # qr detector
        self.main_core.qr_detector.new_qr_detection_data.connect(self.qr_event)

        self.fetch_available_model_databases()

    def disconnect(self):
        """Disconnect from voice and qr."""
        self.main_core.qr_detector.new_qr_detection_data.disconnect(self.qr_event)
        self.main_core.voice_recognizer.text_result.disconnect(self.voice_event)

    def speak(self, text, voice=None):
        """Add text and voice to queue.

        :param text: Text to say.
        :type text: str

        :param voice: Voice name override. (None)
        :type voice: str

            **Example: 'en_US-kristin'**
        """
        self.transcript_lines.append(text)
        self.main_core.speak(text=text, voice=voice)

    @QtCore.pyqtSlot(str)
    def voice_event(self, text):
        """Process a new voice recognition event.

        :param text: The text that was recognized.
        :type text: str
        """
        self.transcript_lines.append(text)
        self.dispatch_event(events.EventType.VOICE, text)

    @QtCore.pyqtSlot(dict)
    def qr_event(self, detection_data):
        """Process a new qr detection.

        :param detection_data: The detection data.
        :type detection_data: dict
        """
        self.dispatch_event(events.EventType.QR, detection_data)

    def dispatch_event(self, event_type, event_data):
        """Dispatch event based on the current state of the title.

        :param event_type: The event type.
        :type event_type: :class:`EventType`

        :param event_data: The data for this event.
        :type event_data: object
        """
        if self.current_title_state == states.TitleState.MENU:
            pass

        elif self.current_title_state == states.TitleState.ARMY:
            if event_type == events.EventType.VOICE:
                text = event_data.lower().strip(".")
                model_info, info_category, similarity = self._current_model_database.find_model_from_text(text)
                self.add_model_to_army(0, events.EventType.VOICE, model_info=model_info)
            elif event_type == events.EventType.QR:
                self.add_model_to_army(0, events.EventType.QR, qrs_list=list(event_data.keys()))

    def fetch_available_model_databases(self) -> None:
        """Fetch and load models databases."""
        self._model_databases_dict = {}
        if not os.path.exists(constants.MODEL_INFO_DATABASE_DIR_PATH):
            return

        for dir_entry in os.scandir(constants.MODEL_INFO_DATABASE_DIR_PATH):
            if dir_entry.is_file():
                if dir_entry.name.endswith(".json"):
                    try:
                        db_name, _ = os.path.splitext(dir_entry.name)
                        self._model_databases_dict[db_name] = midb.ModelInfoDatabase(dir_entry.path)
                    except Exception:
                        print(f"Error: Unable to load database '{db_name}'.")
                        traceback.print_exc()

    def get_model_database_names(self):
        """"""
        return [DATABASE_COMBO_CHOOSE_TEXT] + sorted(self._model_databases_dict.keys())

    def create_model_info_database(self, name: str):
        """"""
        name = re.sub("[^a-zA-Z0-9\\-]", "_", name)
        if name in self._model_databases_dict:
            raise ValueError(f"Model Info Database '{name}' already exists.")
        self._model_databases_dict[name] = midb.ModelInfoDatabase.create_new(name)

    def get_model_info_database(self, name: str) -> midb.ModelInfoDatabase:
        """"""
        return self._model_databases_dict.get(name)

    def start_game(self, model_info_database_name):
        """"""
        self._current_model_database = self._model_databases_dict[model_info_database_name]
        self.speak(constants.NARRATOR_PLAYER_ARMY_COMPOSITION)
        self.current_title_state = states.TitleState.ARMY

    def add_model_to_army(self, player_index: int, event_type: events.EventType, model_info: Optional[midb.ModelInfo] = None, qrs_list: Optional[list[str]] = None):
        """"""
        if event_type is events.EventType.QR and not qrs_list:
            return

        army = self._armies[player_index]
        completed_model_entry = False
        if event_type is events.EventType.QR:
            set_qr_list = [_qr for _modl in army if (_qr := _modl.qr) is not None]
            new_qr_list = [_qr for _qr in qrs_list if _qr not in set_qr_list]
            if not new_qr_list:
                return
            new_qr_value = new_qr_list[0]
        else:
            new_qr_value = None

        for army_model_entry in army:
            if event_type is events.EventType.VOICE and army_model_entry.model_info is None:
                army_model_entry.model_info = model_info
                completed_model_entry = True
                break
            elif event_type is events.EventType.QR and army_model_entry.qr is None:
                army_model_entry.qr = new_qr_value
                completed_model_entry = True
                break
        if not completed_model_entry:
            army.append(midb.ArmyModelEntry(model_info=model_info, qr=new_qr_value))
        self.refresh_armies.emit()
