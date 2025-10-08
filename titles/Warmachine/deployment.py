#
# This file is part of the AiWarmachine distribution (https://github.com/madesjardins/AiWarmachine).
# Copyright (c) 2023-2025 Marc-Antoine Desjardins.
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
"""Deployment class."""

import numpy as np
import cv2 as cv
from PyQt6 import QtCore, QtGui


class Deployment(QtCore.QObject):
    """Deployment phase manager.

    Handles the deployment phase where players place their armies in designated zones.
    Player deploys in first 3 inches of left side (cyan zone).
    Opponent deploys in first 4 inches of right side (pink zone).
    """

    deployment_completed = QtCore.pyqtSignal()

    def __init__(self, title_core):
        """Initialize the deployment manager.

        :param title_core: The title core.
        :type title_core: :class:`TitleCore`
        """
        super().__init__()
        self.title_core = title_core
        self._current_phase = 0  # 0 = player, 1 = opponent
        self._overlay = None
        self._overlay_needs_update = True

        # Start by announcing player deployment
        self._announce_current_phase()

    def _announce_current_phase(self):
        """Announce the current deployment phase to the player."""
        if self._current_phase == 0:
            self.title_core.speak(
                "Please deploy your army in the first 3 inches of the left side of the game board."
            )
        elif self._current_phase == 1:
            self.title_core.speak(
                "Please deploy your opponent's army in the first 4 inches of the right side of the game board."
            )
        self._overlay_needs_update = True

    def handle_voice_command(self, text):
        """Handle voice commands during deployment.

        :param text: The recognized voice command.
        :type text: str
        :return: True if command was handled, False otherwise.
        :rtype: bool
        """
        text_lower = text.lower().strip(".")

        if text_lower == "next army":
            if self._current_phase == 0:
                self._current_phase = 1
                self._announce_current_phase()
                return True
            else:
                self.title_core.speak("Both armies are already configured for deployment.")
                return True

        elif text_lower == "deployment completed":
            self.title_core.speak("Deployment phase is complete. The match will now begin.")
            self.deployment_completed.emit()
            return True

        return False

    def create_deployment_overlay(self):
        """Create the deployment zone overlay for the projector.

        Creates colored rectangles showing deployment zones:
        - Cyan for player (left side, 3 inches deep)
        - Pink for opponent (right side, 4 inches deep)

        :return: Warped overlay image for projector, or None if not calibrated.
        :rtype: :class:`QImage` or None
        """
        game_table = self.title_core.main_core.game_table

        if not game_table.is_calibrated():
            return None

        # Get game table dimensions in pixels
        width, height = game_table.get_effective_table_image_size()

        # Create empty image
        image = np.zeros((height, width, 3), dtype=np.uint8)

        # Convert inches to mm (1 inch = 25.4 mm)
        player_depth_mm = 3 * 25.4  # 3 inches
        opponent_depth_mm = 4 * 25.4  # 4 inches

        # Convert mm to pixels
        player_depth_px = game_table.convert_mm_to_pixel(player_depth_mm, rounded=True)
        opponent_depth_px = game_table.convert_mm_to_pixel(opponent_depth_mm, rounded=True)

        # Player deployment zone (left side, cyan)
        if self._current_phase == 0:
            # Cyan color (BGR format)
            cv.rectangle(
                image,
                (0, 0),
                (player_depth_px, height),
                (255, 255, 0),  # Cyan in BGR
                -1  # Filled rectangle
            )

        # Opponent deployment zone (right side, pink)
        if self._current_phase == 1:
            # Pink color (BGR format)
            cv.rectangle(
                image,
                (width - opponent_depth_px, 0),
                (width, height),
                (203, 192, 255),  # Pink in BGR
                -1  # Filled rectangle
            )

        # Warp the image to projector perspective
        warped_image = game_table.warp_game_to_projector_image(image)

        # Convert to QImage
        return QtGui.QImage(
            warped_image,
            warped_image.shape[1],
            warped_image.shape[0],
            warped_image.strides[0],
            QtGui.QImage.Format.Format_BGR888
        )

    def get_overlay(self):
        """Get the current deployment overlay.

        Creates a new overlay if needed, otherwise returns cached version.

        :return: The deployment overlay image, or None if not available.
        :rtype: :class:`QImage` or None
        """
        if self._overlay_needs_update:
            self._overlay = self.create_deployment_overlay()
            self._overlay_needs_update = False
        return self._overlay
