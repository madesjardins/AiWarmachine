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
from aiwarmachine import common as aiwcom, voice_recognition as aiwvr
from importlib import reload
reload(midb)


class WeaponInfoDialog(QtWidgets.QDialog):
    """"""

    def __init__(
        self,
        voice_recognizer: aiwvr.VoiceRecognizer,
        model_info: midb.ModelInfo = None,
        weapon_info: midb.WeaponInfo = None,
        parent: QtWidgets.QWidget = None
    ) -> None:
        """"""
        super().__init__(parent=parent, flags=QtCore.Qt.WindowType.WindowTitleHint | QtCore.Qt.WindowType.CustomizeWindowHint)
        self.voice_recognizer = voice_recognizer
        self.model_info = model_info
        self.weapon_info = weapon_info
        self._waiting_for_vocal_name = False
        self._previous_name = self.weapon_info.name

        self._init_values()
        self._init_connections()

    def _init_values(self) -> None:
        """"""
        self.ui = uic.loadUi(os.path.join(os.path.dirname(__file__), "ui", "weapon_info_widget.ui"))
        self.setWindowTitle("Weapon Editor")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.ui)
        self.setLayout(layout)

        self.fill_values()

    def _init_connections(self) -> None:
        """"""
        self.voice_recognizer.text_result.connect(self.new_vocal_name)

        self.ui.push_weapon_vocal_names_add.clicked.connect(self._wait_for_vocal_name)
        self.ui.push_weapon_vocal_names_remove.clicked.connect(self.remove_selected_vocal_names)

        self.ui.push_weapon_save.clicked.connect(self.save)
        self.ui.push_weapon_revert.clicked.connect(self.fill_values)
        self.ui.push_weapon_abort.clicked.connect(self.close)

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
        self.ui.push_weapon_vocal_names_add.setEnabled(False)

    @QtCore.pyqtSlot(str)
    def new_vocal_name(self, text: str) -> None:
        """"""
        if self._waiting_for_vocal_name and text:
            text = text.lower().strip(" .")
            if not self.ui.list_weapon_vocal_names.findItems(text, QtCore.Qt.MatchFlag.MatchExactly):
                self.ui.list_weapon_vocal_names.addItem(text)
            self._waiting_for_vocal_name = False
            self.ui.push_weapon_vocal_names_add.setEnabled(True)

    @QtCore.pyqtSlot()
    def save(self) -> None:
        """"""
        current_name = self.ui.edit_weapon_name.text()
        if current_name == "":
            aiwcom.message_box(
                "Error",
                "Please give a name to your weapon",
                info_text=None,
                details_text=None,
                icon_name="Critical",
                button_names_list=["Abort"]
            )

        elif (
            self._previous_name != current_name and
            self.model_info.weapon_exists(current_name)
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
            if self._previous_name != "" and self._previous_name != self.weapon_info.name:
                self.model_info.remove_weapon(self._previous_name)

            self.model_info.update_weapon(self.weapon_info)

        self.close()

    def get_all_vocal_names(self) -> list[str]:
        """"""
        vns_widget = self.ui.list_weapon_vocal_names
        return [vns_widget.item(_row).text() for _row in range(vns_widget.count())]

    def fill_values(self) -> None:
        """"""
        self.ui.edit_weapon_name.setText(self.weapon_info.name)

        self.ui.spin_weapon_qty.setValue(self.weapon_info.qty)

        type_index = self.ui.combo_weapon_type.findText(str(self.weapon_info.typ))
        if type_index > 0:
            self.ui.combo_weapon_type.setCurrentIndex(type_index)
        else:
            self.ui.combo_weapon_type.setCurrentIndex(0)

        self.ui.list_weapon_vocal_names.clear()
        if self.weapon_info.vns:
            self.ui.list_weapon_vocal_names.addItems(self.weapon_info.vns)

        QtWidgets.QCheckBox().setCheckState
        self.ui.double_weapon_rng.setValue(self.weapon_info.rng)
        self.ui.check_weapon_is_spray.setCheckState(QtCore.Qt.CheckState.Checked if self.weapon_info.spray else QtCore.Qt.CheckState.Unchecked)
        self.ui.spin_weapon_rof.setValue(self.weapon_info.rof)
        self.ui.spin_weapon_rofd3.setValue(self.weapon_info.rofd3)
        self.ui.spin_weapon_aoe.setValue(self.weapon_info.aoe)
        self.ui.spin_weapon_pow.setValue(self.weapon_info.pow)
        self.ui.spin_weapon_blast.setValue(self.weapon_info.blast)

        # TODO: advantages and special rules

    def store_info(self) -> None:
        """"""
        # TODO: assert values are all good.
        self.weapon_info.name = self.ui.edit_weapon_name.text()
        self.weapon_info.qty = self.ui.spin_weapon_qty.value()
        self.weapon_info.typ = self.ui.combo_weapon_type.currentText()
        self.weapon_info.vns = self.get_all_vocal_names()

        self.weapon_info.rng = self.ui.double_weapon_rng.value()
        self.weapon_info.spray = self.ui.check_weapon_is_spray.isChecked()
        self.weapon_info.rof = self.ui.spin_weapon_rof.value()
        self.weapon_info.rofd3 = self.ui.spin_weapon_rofd3.value()
        self.weapon_info.aoe = self.ui.spin_weapon_aoe.value()
        self.weapon_info.pow = self.ui.spin_weapon_pow.value()
        self.weapon_info.blast = self.ui.spin_weapon_blast.value()

    @QtCore.pyqtSlot()
    def remove_selected_vocal_names(self) -> None:
        """"""
        all_names_list = self.get_all_vocal_names()
        selected_names_list = [_item.text() for _item in self.ui.list_weapon_vocal_names.selectedItems()]
        remaining_names_list = [_name for _name in all_names_list if _name not in selected_names_list]
        self.ui.list_weapon_vocal_names.clear()
        self.ui.list_weapon_vocal_names.addItems(remaining_names_list)
