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

    closing = QtCore.Signal()

    def __init__(self, parent=None):
        super(UpdateEngineDlg, self).__init__(parent)
        self._ui = Ui_UpdateEngine()
        self._ui.setupUi(self)
        self._ui.ok_button.clicked.connect(self._on_ok_clicked)

    def _on_ok_clicked(self):
        """
        Dismiss the dialog and records the state of the checkbox if clicked.
        """
        if self._ui.never_again_checkbox.isChecked():
            _skip_dialog()
        self.closing.emit()
        self.close()


def _should_skip_dialog():
    """
    :returns: ``True`` if the user dismissed the dialog with "Do not show this again"
        checked in the past, ``False`` otherwise.
    """
    settings_manager = settings.UserSettings(sgtk.platform.current_bundle())
    skip_dialog = settings_manager.retrieve("skip_update_engine_dialog", False)
    return skip_dialog


def _show_dialog(parent):
    """
    Show the dialog warning the user about the deprecation.

    :returns: ``True`` if the user requested the dialog to never be shown
        again, ``False`` otherwise.
    """
    dialog = UpdateEngineDlg(parent)
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()

    return dialog


def show_update_dialog(parent):
    """
    Show the update warning dialog.

    If the user checked "Do not show this dialog again." in the past,
    the method will do nothing.
    """

    if _should_skip_dialog():
        return

    return _show_dialog(parent)