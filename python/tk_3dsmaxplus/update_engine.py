# Copyright (c) 2019 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Displays a message inviting the user to switch their Max engine to tk-3dsmax.
"""

import sgtk
from sgtk.platform.qt import QtCore, QtGui
from .ui.update_engine import Ui_UpdateEngine

settings = sgtk.platform.import_framework("tk-framework-shotgunutils", "settings")


class UpdateEngineDlg(QtGui.QDialog):
    """
    The Update Engine dialog. It displays a deprecation message with a checkbox to
    choose not to see this message ever again.
    """
    hide_tk_title_bar = True

    @classmethod
    def should_skip_dialog(cls):
        """
        :returns: ``True`` if the user dismissed the dialog with "Do not show this again"
            checked in the past, ``False`` otherwise.
        """
        settings_manager = settings.UserSettings(sgtk.platform.current_bundle())
        return settings_manager.retrieve("skip_update_engine_dialog", False)

    def __init__(self, parent=None):
        """
        Init.
        """
        super(UpdateEngineDlg, self).__init__(parent)
        self._ui = Ui_UpdateEngine()
        self._ui.setupUi(self)
        self._ui.ok_button.clicked.connect(self._on_ok_clicked)

    def _on_ok_clicked(self):
        """
        Dismiss the dialog and records the state of the checkbox if clicked.
        """
        if self._ui.never_again_checkbox.isChecked():
            self._skip_dialog()
        self.close()

    def _skip_dialog(self):
        """
        Update user settings so that the dialog is never shown again.
        """
        settings_manager = settings.UserSettings(sgtk.platform.current_bundle())
        settings_manager.store("skip_update_engine_dialog", True)







