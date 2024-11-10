

# class ModelInfoModelTypesDialog(QtWidgets.QDialog):
#     """"""

#     @staticmethod
#     def prompt(types_list: list[str], parent: ModelInfoDialog) -> list[str]:
#         """"""
#         dial = ModelInfoModelTypesDialog(types_list, parent)
#         dial.exec()
#         return dial.types_list

#     def __init__(self, types_list: list[str], parent: ModelInfoDialog) -> None:
#         """"""
#         super().__init__(parent, flags=QtCore.Qt.WindowType.WindowTitleHint | QtCore.Qt.WindowType.CustomizeWindowHint)
#         self._init_uit()
#         self._init_values(types_list)
#         self._init_connections()

#     def _init_uit(self) -> None:
#         """"""
#         self.ui = uic.loadUi(os.path.join(os.path.dirname(__file__), "ui", "model_info_types_widget.ui"))
#         self.setWindowTitle("Model Types")
#         layout = QtWidgets.QVBoxLayout()
#         layout.addWidget(self.ui)
#         self.setLayout(layout)

#         self.types_list = None

#     def _init_connections(self) -> None:
#         """"""
#         self.ui.push_apply.clicked.connect(self.apply)
#         self.ui.push_cancel.clicked.connect(self.close)

#     def _init_values(self, types_list: list[str]) -> None:
#         """"""
#         basic_candidates_list = [e.value for e in midb.ModelInfoBasicType if e.value in types_list]
#         if basic_candidates_list:
#             self.ui.combo_basic.setCurrentIndex(self.ui.combo_basic.findText(basic_candidates_list[0]))

#     @QtCore.pyqtSlot()
#     def apply(self) -> None:
#         """"""
#         self.types_list = [
#             self.ui.combo_basic.currentText()
#         ]
#         self.close()