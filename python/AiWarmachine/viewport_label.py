"""Viewport label widget."""

from PyQt6 import QtCore, QtWidgets


class ViewportLabel(QtWidgets.QLabel):
    """QLabel with mouse event."""

    mouse_press_event = QtCore.pyqtSignal(float, float)
    mouse_drag_event = QtCore.pyqtSignal(float, float)

    def __init__(self, parent=None):
        """Initialize.

        :param parent: Parent Widget. (None)
        :type parent: :class:`QWidget`
        """
        super().__init__(parent=parent)
        self.pix_size = QtCore.QSize(1, 1)
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignLeft)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.is_pressed = False

    def get_normalized_pos(self, pos):
        """Get the normalized position of the mouse event.

        :param pos: Position in pixels.
        :type pos: :class:`QSize`

        :return: Normalized x and y values [0, 1[.
        :rtype: tuple[float, float]
        """
        width = self.pix_size.width()
        height = self.pix_size.height()
        return (
            min(max(0, pos.x() / width), (width - 1) / width),
            min(max(0, pos.y() / height), (height - 1) / height)
        )

    def mousePressEvent(self, event):
        """Mouse press event."""
        self.is_pressed = True
        rel_pos_x, rel_pos_y = self.get_normalized_pos(event.pos())
        self.mouse_press_event.emit(rel_pos_x, rel_pos_y)

    def mouseMoveEvent(self, event):
        """Mouse press event."""
        if self.is_pressed:
            rel_pos_x, rel_pos_y = self.get_normalized_pos(event.pos())
            self.mouse_drag_event.emit(rel_pos_x, rel_pos_y)

    def mouseReleaseEvent(self, event):
        """Mouse release event."""
        self.is_pressed = False

    def setPixmap(self, image):
        """Set Pixmap"""
        if self.pix_size != image.size():
            self.pix_size = image.size()
            self.setFixedSize(self.pix_size)

        super().setPixmap(image)
        self.repaint()
