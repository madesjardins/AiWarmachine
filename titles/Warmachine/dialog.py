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
"""Title dialog to setup mode and scenario."""

import os
import traceback
from functools import partial

from PyQt6 import QtCore, QtWidgets, uic

from . import constants, core, model_info_dialog, model_info_database as midb
from aiwarmachine import common as aiwcom

from importlib import reload
reload(constants)
reload(core)
reload(model_info_dialog)
reload(midb)


class TitleDialog(QtWidgets.QDialog):
    """Game Title Dialog."""

    closing = QtCore.pyqtSignal()

    def __init__(self, title_core: core.TitleCore, parent: QtWidgets.QWidget = None) -> None:
        """Initialize.

        :param title_core: The title core.
        :type title_core: :class:`TitleCore`

        :param parent: The parent widget. (None)
        :type parent: :class:`QWidget`
        """
        super().__init__(parent=parent, flags=QtCore.Qt.WindowType.WindowTitleHint | QtCore.Qt.WindowType.CustomizeWindowHint)

        self.title_core = title_core
        self.parent_widget = parent
        self._overlay_needs_update = True
        self._overlay = None

        self._init_ui()
        self._init_connections()
        self.show()

        self.title_core.speak(constants.NARRATOR_INTRODUCTION)

    def _init_ui(self) -> None:
        """Initialize the UI."""
        self.ui = uic.loadUi(os.path.join(os.path.dirname(__file__), "ui", "title_widget.ui"))
        self.setWindowTitle(f"Warmachine {constants.VERSION}")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.ui)
        self.setLayout(layout)

        self.populate_model_databases()

    def _init_connections(self) -> None:
        """Initialize connections."""
        self.ui.push_exit_title.clicked.connect(self.close)
        self.ui.push_start_game.clicked.connect(self.start_game)

        self.ui.combo_models_database.currentIndexChanged.connect(partial(self.refresh_models, False))
        self.ui.push_models_database_new.clicked.connect(self.create_model_info_database)
        self.ui.push_models_database_save.clicked.connect(self.save_database)
        self.ui.push_models_database_revert.clicked.connect(partial(self.refresh_models, True))

        self.ui.list_models.itemDoubleClicked.connect(self.edit_model)
        self.ui.push_models_create.clicked.connect(self.create_model)
        self.ui.push_edit_model.clicked.connect(self.edit_model)
        self.ui.push_models_delete.clicked.connect(self.remove_models)

        self.title_core.refresh_armies.connect(self.refresh_armies)

    @QtCore.pyqtSlot()
    def close(self) -> None:
        """"""
        super().close()
        self.closing.emit()

    def populate_model_databases(self):
        """"""
        self.ui.combo_models_database.clear()
        db_names_list = self.title_core.get_model_database_names()
        self.ui.combo_models_database.addItems(db_names_list)

    @QtCore.pyqtSlot(bool)
    def refresh_models(self, force_reload: bool = False) -> None:
        """"""
        self.ui.list_models.clear()
        current_model_info_database_name = self.ui.combo_models_database.currentText()
        if (current_model_info_database := self.title_core.get_model_info_database(current_model_info_database_name)) is not None:
            if force_reload:
                current_model_info_database.revert()
            self.ui.list_models.addItems(current_model_info_database.get_names(midb.ModelInfoCategory.INDEPENDENT))

    @QtCore.pyqtSlot()
    def create_model_info_database(self):
        """"""
        db_name, is_valid = QtWidgets.QInputDialog.getText(
            self,
            "Question",
            "What is the name of this new database ?",
        )
        if is_valid:
            try:
                self.title_core.create_model_info_database(db_name)
            except ValueError as err:
                aiwcom.message_box(
                    "Error",
                    err,
                    info_text=None,
                    details_text=None,
                    icon_name="Critical",
                    button_names_list=None
                )
            except Exception:
                aiwcom.message_box(
                    "Error",
                    "An error occured while creating the new database.",
                    info_text=None,
                    details_text=traceback.format_exc(),
                    icon_name="NoIcon",
                    button_names_list=None
                )
            else:
                self.populate_model_databases()

    @QtCore.pyqtSlot()
    def save_database(self) -> None:
        """"""
        current_model_info_database_name = self.ui.combo_models_database.currentText()
        if (current_model_info_database := self.title_core.get_model_info_database(current_model_info_database_name)) is not None:
            current_model_info_database.save()

    def start_game(self):
        """Start this title."""
        self.title_core.start_game(model_info_database_name=self.ui.combo_models_database.currentText())

        # camera_is_calibrated = False
        # if camera := self.core.camera_manager.get_camera():
        #     camera_is_calibrated = camera.is_calibrated()
        # game_table_is_calibrated = self.core.game_table.is_calibrated()

        # if camera_is_calibrated and game_table_is_calibrated:
        #     self.ui.push_titles_launch.setEnabled(False)
        #     self.ui.push_titles_refresh.setEnabled(False)
        #     self.ui.push_titles_stop.setEnabled(True)

        #     self.projector_dialog.disconnect_from_qr_detection()
        #     self.core.launch_title(title_name, self)
        # else:
        #     common.message_box(
        #         "Warning",
        #         "Please calibrate your camera and table before launching a title.",
        #         icon_name="Warning",
        #         button_names_list=['Close']
        #     )

    @QtCore.pyqtSlot()
    def create_model(self):
        """"""
        current_model_info_database_name = self.ui.combo_models_database.currentText()
        if (current_model_info_database := self.title_core.get_model_info_database(current_model_info_database_name)) is not None:
            new_model_info = midb.ModelInfo(icat=midb.ModelInfoCategory.INDEPENDENT)
            model_dial = model_info_dialog.ModelInfoDialog(
                voice_recognizer=self.title_core.main_core.voice_recognizer,
                model_info_database=current_model_info_database,
                parent=self,
                model_info=new_model_info,
            )
            model_dial.exec()
            self.refresh_models()

    @QtCore.pyqtSlot()
    def edit_model(self):
        """"""
        current_model_info_database_name = self.ui.combo_models_database.currentText()
        if (current_model_info_database := self.title_core.get_model_info_database(current_model_info_database_name)) is not None:
            selected_model_names_list = self.get_selected_model_names()
            if len(selected_model_names_list) != 1:
                aiwcom.message_box(
                    "Error",
                    "Only one model can be edited at a time.",
                    info_text=None,
                    details_text=None,
                    icon_name="Error",
                    button_names_list=["Close"]
                )
                return
            model_name = selected_model_names_list[0]
            model_info = current_model_info_database.get(model_name, info_category=midb.ModelInfoCategory.INDEPENDENT)
            model_dial = model_info_dialog.ModelInfoDialog(
                voice_recognizer=self.title_core.main_core.voice_recognizer,
                model_info_database=current_model_info_database,
                parent=self,
                model_info=model_info,
            )
            model_dial.exec()
            self.refresh_models()

    def remove_models(self) -> None:
        """"""
        current_model_info_database_name = self.ui.combo_models_database.currentText()
        if (current_model_info_database := self.title_core.get_model_info_database(current_model_info_database_name)) is not None:
            selected_model_names_list = self.get_selected_model_names()
            if selected_model_names_list:
                current_model_info_database.remove_multi(selected_model_names_list)
                self.refresh_models()

    def get_selected_model_names(self) -> list[str]:
        """"""
        return [_item.text() for _item in self.ui.list_models.selectedItems()]

    @QtCore.pyqtSlot()
    def refresh_armies(self):
        """"""
        self.ui.list_armies_player.clear()
        self.ui.list_armies_opponent.clear()
        for army_index, army in enumerate(self.title_core._armies):
            if army_index == 0:
                list_army_widget = self.ui.list_armies_player
            else:
                list_army_widget = self.ui.list_armies_opponent

            for army_model_entry in army:
                model_name = qr = "TBD"
                if army_model_entry.model_info is not None:
                    model_name = f"'{army_model_entry.model_info.name}'"
                if army_model_entry.qr is not None:
                    qr = f"'{army_model_entry.qr}'"
                list_army_widget.addItem(f"Name: {model_name}, QR: {qr}.")
