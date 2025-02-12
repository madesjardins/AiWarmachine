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
from . import weapon_info_dialog
from aiwarmachine import common as aiwcom, voice_recognition as aiwvr
from importlib import reload
reload(midb)
reload(weapon_info_dialog)


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

        self._init_ui()
        self._init_values()
        self._init_connections()

    def _init_ui(self) -> None:
        """"""
        self.ui = uic.loadUi(os.path.join(os.path.dirname(__file__), "ui", "model_info_widget.ui"))
        self.setWindowTitle("Model Editor")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.ui)
        self.setLayout(layout)

    @QtCore.pyqtSlot()
    def _init_values(self) -> None:
        """"""
        self._reset_working_model()
        self.fill_values()

    def _init_connections(self) -> None:
        """"""
        self.voice_recognizer.text_result.connect(self.new_vocal_name)

        self.ui.push_model_vocal_names_add.clicked.connect(self._wait_for_vocal_name)
        self.ui.push_model_vocal_names_remove.clicked.connect(self.remove_selected_vocal_names)

        self.ui.push_model_save.clicked.connect(self.save)
        self.ui.push_model_revert.clicked.connect(self._init_values)
        self.ui.push_model_close.clicked.connect(self.close)

        self.ui.push_model_weapons_add.clicked.connect(self.add_weapon)
        self.ui.push_model_weapons_edit.clicked.connect(self.edit_selected_weapon)
        self.ui.list_model_weapons.itemDoubleClicked.connect(self.edit_selected_weapon)
        self.ui.push_model_weapons_remove.clicked.connect(self.remove_selected_weapons)

    def _reset_working_model(self) -> None:
        """"""
        self._working_model_info = midb.ModelInfo.from_dict(self.model_info.as_dict())

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
            self.model_info_database.exists(current_name, self._working_model_info.icat)
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
            if self._previous_name != "" and self._previous_name != self._working_model_info.name:
                self.model_info_database.remove(self._previous_name, self._working_model_info.icat)

            self.model_info.update(self._working_model_info.as_dict())
            self.model_info_database.update(self.model_info)

    def get_all_vocal_names(self) -> list[str]:
        """"""
        vns_widget = self.ui.list_model_vocal_names
        return [vns_widget.item(_row).text() for _row in range(vns_widget.count())]

    def get_all_weapon_names(self) -> list[str]:
        """"""
        wpns_widget = self.ui.list_model_weapons
        return [wpns_widget.item(_row).text() for _row in range(wpns_widget.count())]

    def fill_values(self) -> None:
        """"""
        self.ui.edit_model_name.setText(self._working_model_info.name)
        self.ui.edit_model_short_name.setText(self._working_model_info.snm)

        fact_index = self.ui.combo_model_faction.findText(str(self._working_model_info.fact))
        if fact_index > 0:
            self.ui.combo_model_faction.setCurrentIndex(fact_index)
        else:
            self.ui.combo_model_faction.setCurrentIndex(0)

        btype_index = self.ui.combo_model_basic_type.findText(str(self._working_model_info.btyp))
        if btype_index > 0:
            self.ui.combo_model_basic_type.setCurrentIndex(btype_index)
        else:
            self.ui.combo_model_basic_type.setCurrentIndex(0)

        bsz_index = self.ui.combo_model_base_size.findText(str(self._working_model_info.bsz))
        if bsz_index > 0:
            self.ui.combo_model_base_size.setCurrentIndex(bsz_index)
        else:
            self.ui.combo_model_base_size.setCurrentIndex(0)

        self.ui.spin_model_cost.setValue(self._working_model_info.cost)

        self.ui.check_model_is_character.setCheckState(QtCore.Qt.CheckState.Checked if self._working_model_info.char else QtCore.Qt.CheckState.Unchecked)
        if self._working_model_info.char:
            self.ui.spin_model_fa.setValue(1)
        else:
            self.ui.spin_model_fa.setValue(self._working_model_info.fa)

        self.ui.list_model_vocal_names.clear()
        if self._working_model_info.vns:
            self.ui.list_model_vocal_names.addItems(self._working_model_info.vns)
        self.ui.edit_model_keywords.setText(self._working_model_info.kws)

        self.ui.spin_model_stats_spd.setValue(self._working_model_info.spd)
        self.ui.spin_model_stats_aat.setValue(self._working_model_info.aat)
        self.ui.spin_model_stats_mat.setValue(self._working_model_info.mat)
        self.ui.spin_model_stats_rat.setValue(self._working_model_info.rat)
        self.ui.spin_model_stats_def.setValue(self._working_model_info.def_)
        self.ui.spin_model_stats_arm.setValue(self._working_model_info.arm)
        self.ui.spin_model_stats_arc.setValue(self._working_model_info.arc)
        self.ui.spin_model_stats_ctrl.setValue(self._working_model_info.ctrl)
        self.ui.spin_model_stats_fury.setValue(self._working_model_info.fury)
        self.ui.spin_model_stats_thr.setValue(self._working_model_info.thr)

        self.ui.spin_model_health.setValue(self._working_model_info.hp.value)

        self.fill_weapons()

    def store_info(self) -> None:
        """"""
        # TODO: assert values are all good.
        self._working_model_info.name = self.ui.edit_model_name.text()
        self._working_model_info.snm = self.ui.edit_model_short_name.text()
        self._working_model_info.fact = self.ui.combo_model_faction.currentText()
        self._working_model_info.btyp = self.ui.combo_model_basic_type.currentText()
        self._working_model_info.cost = self.ui.spin_model_cost.value()
        self._working_model_info.char = self.ui.check_model_is_character.isChecked()
        if self._working_model_info.char:
            self._working_model_info.fa = 1
        else:
            self._working_model_info.fa = self.ui.spin_model_fa.value()
        self._working_model_info.bsz = int(self.ui.combo_model_base_size.currentText())
        self._working_model_info.vns = self.get_all_vocal_names()
        self._working_model_info.kws = self.ui.edit_model_keywords.text()

        self._working_model_info.spd = self.ui.spin_model_stats_spd.value()
        self._working_model_info.aat = self.ui.spin_model_stats_aat.value()
        self._working_model_info.mat = self.ui.spin_model_stats_mat.value()
        self._working_model_info.rat = self.ui.spin_model_stats_rat.value()
        self._working_model_info.def_ = self.ui.spin_model_stats_def.value()
        self._working_model_info.arm = self.ui.spin_model_stats_arm.value()
        self._working_model_info.arc = self.ui.spin_model_stats_arc.value()
        self._working_model_info.ctrl = self.ui.spin_model_stats_ctrl.value()
        self._working_model_info.fury = self.ui.spin_model_stats_fury.value()
        self._working_model_info.thr = self.ui.spin_model_stats_thr.value()

        # TODO: Other health types
        self._working_model_info.hp.typ = midb.HealthType.VALUE
        self._working_model_info.hp.value = self.ui.spin_model_health.value()

    @QtCore.pyqtSlot()
    def remove_selected_vocal_names(self) -> None:
        """"""
        all_names_list = self.get_all_vocal_names()
        selected_names_list = [_item.text() for _item in self.ui.list_model_vocal_names.selectedItems()]
        remaining_names_list = [_name for _name in all_names_list if _name not in selected_names_list]
        self.ui.list_model_vocal_names.clear()
        self.ui.list_model_vocal_names.addItems(remaining_names_list)

    def fill_weapons(self) -> None:
        """"""
        all_names_list = [_wpn.name for _wpn in self._working_model_info.wpns]
        self.ui.list_model_weapons.clear()
        self.ui.list_model_weapons.addItems(all_names_list)

    @QtCore.pyqtSlot()
    def add_weapon(self) -> None:
        """"""
        new_weapon_info = midb.WeaponInfo()
        weapon_dial = weapon_info_dialog.WeaponInfoDialog(
            voice_recognizer=self.voice_recognizer,
            model_info=self._working_model_info,
            parent=self,
            weapon_info=new_weapon_info,
        )
        weapon_dial.exec()
        self.fill_weapons()

    def get_selected_weapon_names(self) -> list[str]:
        """"""
        return [_item.text().split(",")[0].strip() for _item in self.ui.list_model_weapons.selectedItems()]

    def get_selected_weapon_indices(self) -> list[str]:
        """"""
        selected_weapon_names_list = self.get_selected_weapon_names()
        return [_index for _index, _wpn in enumerate(self._working_model_info.wpns) if _wpn.name in selected_weapon_names_list]

    @QtCore.pyqtSlot()
    def edit_selected_weapon(self) -> None:
        """"""
        selected_weapon_indices_list = self.get_selected_weapon_indices()
        if not selected_weapon_indices_list:
            return
        weapon_info = self._working_model_info.wpns[selected_weapon_indices_list[0]]
        weapon_dial = weapon_info_dialog.WeaponInfoDialog(
            voice_recognizer=self.voice_recognizer,
            model_info=self._working_model_info,
            parent=self,
            weapon_info=weapon_info,
        )
        weapon_dial.exec()
        self.fill_weapons()

    @QtCore.pyqtSlot()
    def remove_selected_weapons(self) -> None:
        """"""
        selected_weapon_indices_list = self.get_selected_weapon_indices()
        if not selected_weapon_indices_list:
            return
        selected_weapon_indices_list.sort(reverse=True)
        for index in selected_weapon_indices_list:
            del self._working_model_info.wpns[index]

        self.fill_weapons()
        # all_names_list = self.get_all_weapon_names()
        # selected_names_list = [_item.text() for _item in self.ui.list_model_weapons.selectedItems()]
        # remaining_names_list = [_name for _name in all_names_list if _name not in selected_names_list]
        # self.ui.list_model_weapons.clear()
        # self.ui.list_model_weapons.addItems(remaining_names_list)
