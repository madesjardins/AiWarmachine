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
"""Model creation dialog."""

import os
import traceback
from typing import Any

from PyQt6 import QtCore, QtWidgets, uic

from . import model_info_database as midb
from aiwarmachine import common as aiwcom, voice_recognition as aiwvr, constants as aiwconst
from importlib import reload
reload(midb)


class ModelInfoDialog(QtWidgets.QDialog):
    """"""

    def __init__(
        self,
        voice_recognizer: aiwvr.VoiceRecognizer,
        model_info_database: midb.ModelInfoDatabase,
        model_info: midb.ModelInfo = None,
        parent: QtWidgets.QWidget = None
    ) -> None:
        """"""
        super().__init__(parent=parent, flags=QtCore.Qt.WindowType.WindowTitleHint | QtCore.Qt.WindowType.CustomizeWindowHint)
        self.voice_recognizer = voice_recognizer
        self.model_info_database = model_info_database
        self.model_info = model_info
        self._waiting_for_vocal_name = False
        self._previous_name = self.model_info.name

        self._init_values()
        self._init_connections()

    def _init_values(self) -> None:
        """"""
        self.ui = uic.loadUi(os.path.join(os.path.dirname(__file__), "ui", "model_info_widget.ui"))
        self.setWindowTitle("Model Editor")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.ui)
        self.setLayout(layout)

        self.fill_values()

    def _init_connections(self) -> None:
        """"""
        self.voice_recognizer.text_result.connect(self.new_vocal_name)

        self.ui.push_model_vocal_names_add.clicked.connect(self._wait_for_vocal_name)
        self.ui.push_model_vocal_names_remove.clicked.connect(self.remove_selected_vocal_names)

        self.ui.push_model_save.clicked.connect(self.save)
        self.ui.push_model_revert.clicked.connect(self.fill_values)
        self.ui.push_model_close.clicked.connect(self.close)

        self.ui.push_model_types_edit.clicked.connect(self.edit_model_types)

    def closeEvent(self, a0: Any) -> None:
        """"""
        try:
            self.voice_recognizer.text_result.disconnect(self.new_vocal_name)
        except Exception:
            traceback.print_exc()
        return super().closeEvent(a0)

    @QtCore.pyqtSlot()
    def _wait_for_vocal_name(self) -> None:
        """"""
        self._waiting_for_vocal_name = True
        self.ui.push_model_vocal_names_add.setEnabled(False)

    @QtCore.pyqtSlot(str)
    def new_vocal_name(self, text: str) -> None:
        """"""
        if self._waiting_for_vocal_name and text:
            text = text.lower().strip(" .")
            if not self.ui.list_model_vocal_names.findItems(text, QtCore.Qt.MatchFlag.MatchExactly):
                self.ui.list_model_vocal_names.addItem(text)
            self._waiting_for_vocal_name = False
            self.ui.push_model_vocal_names_add.setEnabled(True)

    @QtCore.pyqtSlot()
    def save(self) -> None:
        """"""
        current_name = self.ui.edit_model_name.text()
        if current_name == "":
            aiwcom.message_box(
                "Error",
                "Please give a name to your model/unit",
                info_text=None,
                details_text=None,
                icon_name="Critical",
                button_names_list=["Abort"]
            )

        elif (
            self._previous_name != current_name and
            self.model_info_database.exists(current_name, self.model_info.ityp)
        ):
            aiwcom.message_box(
                "Error",
                "Name already exist.",
                info_text=None,
                details_text=None,
                icon_name="Critical",
                button_names_list=["Abort"]
            )

        else:
            self.store_info()
            if self._previous_name != "" and self._previous_name != self.model_info.name:
                self.model_info_database.remove(self._previous_name, self.model_info.ityp)

            self.model_info_database.update(self.model_info)

            # prevent changes on database without a save
            self.model_info = self.model_info.duplicate()

    def get_all_vocal_names(self) -> list[str]:
        """"""
        vns_widget = self.ui.list_model_vocal_names
        return [vns_widget.item(_row).text() for _row in range(vns_widget.count())]

    def get_types(self) -> list[str]:
        """"""
        return [_t for _t in self.ui.edit_model_types.text().split(aiwconst.CSV_DELIMITER) if _t]

    def fill_values(self) -> None:
        """"""
        self.ui.edit_model_name.setText(self.model_info.name)
        self.ui.edit_model_short_name.setText(self.model_info.snm)
        bsz_index = self.ui.combo_model_base_size.findText(str(self.model_info.bsz))
        if bsz_index > 0:
            self.ui.combo_model_base_size.setCurrentIndex(bsz_index)
        else:
            self.ui.combo_model_base_size.setCurrentIndex(0)
        self.ui.spin_model_cost.setValue(self.model_info.cost)
        self.ui.spin_model_fa.setValue(self.model_info.fa)
        self.ui.list_model_vocal_names.clear()
        if self.model_info.vns:
            self.ui.list_model_vocal_names.addItems(self.model_info.vns)
        self.ui.edit_model_types.setText(aiwconst.CSV_DELIMITER.join(self.model_info.typs))

    def store_info(self) -> None:
        """"""
        self.model_info.name = self.ui.edit_model_name.text()
        self.model_info.snm = self.ui.edit_model_short_name.text()
        self.model_info.cost = self.ui.spin_model_cost.value()
        self.model_info.fa = self.ui.spin_model_fa.value()
        self.model_info.bsz = int(self.ui.combo_model_base_size.currentText())
        self.model_info.vns = self.get_all_vocal_names()
        self.model_info.typs = self.get_types()

    @QtCore.pyqtSlot()
    def remove_selected_vocal_names(self) -> None:
        """"""
        all_names_list = self.get_all_vocal_names()
        selected_names_list = [_item.text() for _item in self.ui.list_model_vocal_names.selectedItems()]
        remaining_names_list = [_name for _name in all_names_list if _name not in selected_names_list]
        self.ui.list_model_vocal_names.clear()
        self.ui.list_model_vocal_names.addItems(remaining_names_list)

    @QtCore.pyqtSlot()
    def edit_model_types(self) -> None:
        """"""
        edited_types = ModelInfoModelTypesDialog.prompt(types_list=self.get_types(), parent=self)
        if edited_types is not None:
            self.model_info.typs = edited_types
            self.ui.edit_model_types.setText(aiwconst.CSV_DELIMITER.join(self.model_info.typs))


class ModelInfoModelTypesDialog(QtWidgets.QDialog):
    """"""

    @staticmethod
    def prompt(types_list: list[str], parent: ModelInfoDialog) -> list[str]:
        """"""
        dial = ModelInfoModelTypesDialog(types_list, parent)
        dial.exec()
        return dial.types_list

    def __init__(self, types_list: list[str], parent: ModelInfoDialog) -> None:
        """"""
        super().__init__(parent, flags=QtCore.Qt.WindowType.WindowTitleHint | QtCore.Qt.WindowType.CustomizeWindowHint)
        self._init_uit()
        self._init_values(types_list)
        self._init_connections()

    def _init_uit(self) -> None:
        """"""
        self.ui = uic.loadUi(os.path.join(os.path.dirname(__file__), "ui", "model_info_model_types_widget.ui"))
        self.setWindowTitle("Model Types")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.ui)
        self.setLayout(layout)

        self.types_list = None

    def _init_connections(self) -> None:
        """"""
        self.ui.push_apply.clicked.connect(self.apply)
        self.ui.push_cancel.clicked.connect(self.close)

    def _init_values(self, types_list: list[str]) -> None:
        """"""
        basic_candidates_list = [e.value for e in midb.ModelInfoModelTypeBasic if e.value in types_list]
        if basic_candidates_list:
            self.ui.combo_basic.setCurrentIndex(self.ui.combo_basic.findText(basic_candidates_list[0]))

    @QtCore.pyqtSlot()
    def apply(self) -> None:
        """"""
        self.types_list = [
            self.ui.combo_basic.currentText()
        ]
        self.close()
